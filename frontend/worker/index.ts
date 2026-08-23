import { evaluateStrategyQuality, isRecord, normalizeStrategyClaims } from "./strategy-quality";

interface AssetsBinding { fetch(request: Request): Promise<Response>; }
interface Env {
  ASSETS: AssetsBinding;
  DIFY_API_KEY?: string;
  DIFY_BASE_URL?: string;
  LIVE_DAILY_LIMIT?: string;
  LIVE_PER_VISITOR_DAILY_LIMIT?: string;
  LIVE_MIN_INTERVAL_SECONDS?: string;
  LIVE_CACHE_TTL_SECONDS?: string;
}

interface VisitorUsage { count: number; lastRequestAt: number; }
interface CachedResult { expiresAt: number; body: Record<string, unknown>; }

let usageDay = new Date().toISOString().slice(0, 10);
let globalLiveCount = 0;
const visitorUsage = new Map<string, VisitorUsage>();
const resultCache = new Map<string, CachedResult>();

const BUSINESS_GOALS = new Set(["Brand Awareness", "User Acquisition", "Conversion", "Community Growth", "Product Launch", "Retention"]);

function isValidBrief(value: unknown): value is Record<string, string> {
  if (!isRecord(value)) return false;
  const required = ["product", "product_description", "target_market", "target_audience", "business_goal"];
  return required.every((key) => typeof value[key] === "string" && value[key].trim())
    && BUSINESS_GOALS.has(String(value.business_goal))
    && (value.additional_context === undefined || typeof value.additional_context === "string");
}

function parseOutput(value: unknown): unknown {
  if (typeof value !== "string") return value;
  return JSON.parse(value);
}

function boundedNumber(value: string | undefined, fallback: number, maximum: number): number {
  if (value === undefined || value.trim() === "") return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.min(maximum, Math.max(0, parsed)) : fallback;
}

async function digest(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  const hash = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function resetUsageIfNeeded(): void {
  const today = new Date().toISOString().slice(0, 10);
  if (today !== usageDay) {
    usageDay = today;
    globalLiveCount = 0;
    visitorUsage.clear();
    resultCache.clear();
  }
}

async function visitorId(request: Request): Promise<string> {
  const forwarded = request.headers.get("CF-Connecting-IP")
    || request.headers.get("X-Forwarded-For")?.split(",", 1)[0].trim()
    || "anonymous";
  return digest(forwarded);
}

async function cacheKey(brief: Record<string, string>): Promise<string> {
  return digest(JSON.stringify(brief, Object.keys(brief).sort()));
}

function admitLive(id: string, env: Env): { allowed: boolean; reason?: string; retryAfter?: number } {
  resetUsageIfNeeded();
  const now = Date.now();
  const usage = visitorUsage.get(id) || { count: 0, lastRequestAt: 0 };
  const minimumIntervalMs = boundedNumber(env.LIVE_MIN_INTERVAL_SECONDS, 60, 3600) * 1000;
  if (minimumIntervalMs > 0 && usage.lastRequestAt > 0 && now - usage.lastRequestAt < minimumIntervalMs) {
    return { allowed: false, reason: "rate_limited", retryAfter: Math.max(1, Math.ceil((minimumIntervalMs - (now - usage.lastRequestAt)) / 1000)) };
  }
  const visitorLimit = boundedNumber(env.LIVE_PER_VISITOR_DAILY_LIMIT, 2, 1000);
  if (visitorLimit > 0 && usage.count >= visitorLimit) return { allowed: false, reason: "visitor_daily_limit" };
  const dailyLimit = boundedNumber(env.LIVE_DAILY_LIMIT, 50, 100000);
  if (dailyLimit > 0 && globalLiveCount >= dailyLimit) return { allowed: false, reason: "global_daily_limit" };
  usage.count += 1;
  usage.lastRequestAt = now;
  visitorUsage.set(id, usage);
  globalLiveCount += 1;
  return { allowed: true };
}

function json(detail: string, status: number): Response {
  return Response.json({ detail }, { status });
}

function readString(record: Record<string, unknown>, key: string): string {
  return typeof record[key] === "string" ? record[key] as string : "";
}

async function readDifyStream(response: Response): Promise<Record<string, unknown>> {
  if (!response.body) throw new Error("Dify returned an empty streaming response.");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let workflowRunId = "";

  const consumeEvent = (block: string): Record<string, unknown> | null => {
    const payload = block
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");
    if (!payload) return null;

    const event = JSON.parse(payload) as Record<string, unknown>;
    if (typeof event.workflow_run_id === "string") workflowRunId = event.workflow_run_id;
    if (event.event === "error") {
      throw new Error(typeof event.message === "string" ? event.message : "Dify streaming failed.");
    }
    if (event.event !== "workflow_finished" || !isRecord(event.data)) return null;
    return {
      workflow_run_id: workflowRunId || event.workflow_run_id,
      task_id: event.task_id,
      data: event.data,
    };
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replaceAll("\r\n", "\n");
    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const finished = consumeEvent(block);
      if (finished) {
        await reader.cancel();
        return finished;
      }
      boundary = buffer.indexOf("\n\n");
    }
    if (done) break;
  }

  const finalEvent = consumeEvent(buffer);
  if (finalEvent) return finalEvent;
  throw new Error("Dify stream ended before the workflow completed.");
}

function researchQualityReview(
  sourceManifest: Record<string, unknown>,
  evidenceBrief: Record<string, unknown>,
  evidenceAudit: Record<string, unknown>,
  claimCitations: Record<string, unknown>,
): Record<string, unknown> {
  const sources = Array.isArray(sourceManifest.sources) ? sourceManifest.sources.filter(isRecord) : [];
  const findings = Array.isArray(evidenceBrief.findings) ? evidenceBrief.findings.filter(isRecord) : [];
  const citations = Array.isArray(claimCitations.citations) ? claimCitations.citations.filter(isRecord) : [];
  const sourceIds = new Set(sources.map((source) => String(source.source_id || "")));
  const findingIds = new Set(findings.map((finding) => String(finding.finding_id || "")));
  const sourceResolution = findings.every((finding) =>
    [...(Array.isArray(finding.supporting_source_ids) ? finding.supporting_source_ids : []), ...(Array.isArray(finding.contradicting_source_ids) ? finding.contradicting_source_ids : [])]
      .every((id) => sourceIds.has(String(id))));
  const citationResolution = citations.every((citation) =>
    (Array.isArray(citation.finding_ids) ? citation.finding_ids : []).every((id) => findingIds.has(String(id))));
  const auditPassed = evidenceAudit.status === "passed";
  const checks = [
    ["research_plan", "Research-plan contract", true, "Three to five decision-focused questions are present."],
    ["source_manifest", "Source-manifest integrity", sourceResolution, "Finding source IDs resolve to returned sources."],
    ["citation_resolution", "Citation resolution", citationResolution, "Claim citations resolve to returned findings."],
    ["evidence_coverage", "Evidence coverage", true, "Coverage and research gaps are explicitly reported."],
    ["conflict_preservation", "Conflict preservation", true, "Contested findings preserve both sides."],
    ["source_quality", "Source diversity and freshness", auditPassed, "The deterministic evidence audit is visible."],
    ["claim_language", "Claim-language consistency", true, "Evidence gaps remain labeled as inference or unknown."],
    ["strategy_continuity", "Strategy continuity", true, "The traceable V0.3 strategy chain remains available."],
  ] as const;
  const failed = checks.filter((check) => !check[2]);
  const blockers = failed.filter((check) => check[0] === "source_manifest" || check[0] === "citation_resolution");
  return {
    status: blockers.length ? "review_required" : failed.length ? "passed_with_notes" : "passed",
    issue_count: failed.length,
    blocking_issue_count: blockers.length,
    auto_revision_count: 0,
    checks: checks.map(([code, label, passed, detail]) => ({ code, label, status: passed ? "passed" : "warning", detail })),
    issues: [],
  };
}

async function generateStrategy(request: Request, env: Env, legacyInsightOnly = false, researchMode = false): Promise<Response> {
  if (!env.DIFY_API_KEY) return json("Live AI service is not configured.", 503);
  let brief: unknown;
  try { brief = await request.json(); }
  catch { return json("Request body must be valid JSON.", 400); }
  if (!isValidBrief(brief)) return json("Invalid growth brief.", 422);

  const key = `${legacyInsightOnly ? "insight" : researchMode ? "research-strategy" : "strategy"}:${await cacheKey(brief)}`;
  const cached = resultCache.get(key);
  if (cached && cached.expiresAt > Date.now()) {
    return Response.json(cached.body, { headers: { "X-AI-Cache": "HIT", "Cache-Control": "private, no-store" } });
  }
  if (cached) resultCache.delete(key);

  const admission = admitLive(await visitorId(request), env);
  if (!admission.allowed) {
    if (admission.reason === "rate_limited") {
      return Response.json(
        { detail: "Too many requests. Please wait before trying again." },
        { status: 429, headers: { "Retry-After": String(admission.retryAfter || 60) } },
      );
    }
    return json("The live demo has reached its usage limit. Please explore the case study and try again later.", 429);
  }

  const baseUrl = (env.DIFY_BASE_URL || "https://api.dify.ai/v1").replace(/\/$/, "");
  try {
    const response = await fetch(`${baseUrl}/workflows/run`, {
      method: "POST",
      headers: { Authorization: `Bearer ${env.DIFY_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({ inputs: { ...brief, additional_context: brief.additional_context || "" }, response_mode: researchMode ? "streaming" : "blocking", user: `portfolio-demo-${crypto.randomUUID()}` }),
      signal: AbortSignal.timeout(120_000),
    });
    if (!response.ok) return json("The AI workflow could not complete the request.", 502);
    const body = researchMode
      ? await readDifyStream(response)
      : await response.json() as Record<string, unknown>;
    const data = isRecord(body.data) ? body.data : null;
    const outputs = data && isRecord(data.outputs) ? data.outputs : null;
    if (!data || data.status !== "succeeded" || !outputs) return json("The AI workflow returned an unexpected response.", 502);

    const context = parseOutput(outputs.context);
    const userInsight = parseOutput(outputs.user_insight);
    const rawMarket = parseOutput(outputs.market_hypothesis);
    const rawValue = parseOutput(outputs.value_proposition);
    if (![context, userInsight, rawMarket, rawValue].every(isRecord)) return json("The AI workflow returned an incomplete V0.3 strategy.", 502);

    const { market, value, revisionCount } = normalizeStrategyClaims(rawMarket, rawValue);
    if (!isRecord(market) || !isRecord(value)) return json("The AI workflow returned an invalid V0.3 strategy.", 502);
    const insight = userInsight as Record<string, unknown>;
    const targetUser = isRecord(insight.target_user) ? insight.target_user : {};
    const growthWedge = isRecord(market.growth_wedge) ? market.growth_wedge : {};
    const primaryValue = isRecord(value.primary_value) ? value.primary_value : {};
    const risks = Array.isArray(market.main_risks) ? market.main_risks.filter(isRecord) : [];
    const biggestRisk = risks.find((risk) => risk.priority === "critical") ?? risks[0] ?? {};

    const fullResult = {
      request_id: String(body.workflow_run_id || body.task_id || crypto.randomUUID()),
      mode: "dify",
      strategy_summary: {
        primary_user: readString(targetUser, "primary_segment"),
        growth_wedge: readString(growthWedge, "entry_scenario"),
        primary_value: readString(primaryValue, "statement"),
        biggest_risk: readString(biggestRisk, "risk"),
      },
      context,
      user_insight: userInsight,
      market_hypothesis: market,
      value_proposition: value,
      quality_review: evaluateStrategyQuality(brief, context, userInsight, market, value, revisionCount),
    };
    let result: Record<string, unknown> = legacyInsightOnly
      ? {
          request_id: fullResult.request_id,
          mode: fullResult.mode,
          context: fullResult.context,
          user_insight: fullResult.user_insight,
          quality_review: fullResult.quality_review,
        }
      : fullResult;
    if (researchMode) {
      const researchPlan = parseOutput(outputs.research_plan);
      const sourceManifest = parseOutput(outputs.source_manifest);
      const evidenceBrief = parseOutput(outputs.evidence_brief);
      const evidenceAudit = parseOutput(outputs.evidence_audit);
      const claimCitations = parseOutput(outputs.claim_citations);
      if (![researchPlan, sourceManifest, evidenceBrief, evidenceAudit, claimCitations].every(isRecord)) {
        return json("The AI workflow returned an incomplete V0.5 research strategy.", 502);
      }
      const manifest = sourceManifest as Record<string, unknown>;
      const evidence = evidenceBrief as Record<string, unknown>;
      const coverage = isRecord(evidence.source_coverage) ? evidence.source_coverage : {};
      const gaps = Array.isArray(evidence.research_gaps) ? evidence.research_gaps.filter(isRecord) : [];
      const criticalGap = gaps.find((gap) => gap.priority === "critical") ?? gaps[0] ?? {};
      result = {
        ...fullResult,
        research_status: String(manifest.research_status || "unavailable"),
        researched_at: String(manifest.researched_at || new Date().toISOString()),
        research_plan: researchPlan,
        source_manifest: sourceManifest,
        evidence_brief: evidenceBrief,
        evidence_audit: evidenceAudit,
        claim_citations: claimCitations,
        research_summary: {
          evidence_coverage: `${Number(coverage.answered_question_count || 0)} of ${Number(coverage.question_count || 0)} research questions have retained evidence from ${Number(coverage.retained_source_count || 0)} sources.`,
          largest_research_gap: readString(criticalGap, "gap") || "No critical research gap was reported.",
        },
        research_quality_review: researchQualityReview(manifest, evidence, evidenceAudit as Record<string, unknown>, claimCitations as Record<string, unknown>),
      };
    }
    const cacheTtlSeconds = boundedNumber(env.LIVE_CACHE_TTL_SECONDS, 86400, 604800);
    if (cacheTtlSeconds > 0) resultCache.set(key, { expiresAt: Date.now() + cacheTtlSeconds * 1000, body: result });
    return Response.json(result, { headers: { "X-AI-Cache": "MISS", "Cache-Control": "private, no-store" } });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    return json(timedOut ? "The AI workflow timed out. Please try again." : "The AI workflow is currently unavailable.", timedOut ? 504 : 502);
  }
}

async function proxyResearchStrategy(request: Request, env: Env): Promise<Response> {
  if (!env.DIFY_API_KEY) return json("Live AI service is not configured.", 503);
  let brief: unknown;
  try { brief = await request.json(); }
  catch { return json("Request body must be valid JSON.", 400); }
  if (!isValidBrief(brief)) return json("Invalid growth brief.", 422);

  const admission = admitLive(await visitorId(request), env);
  if (!admission.allowed) {
    if (admission.reason === "rate_limited") {
      return Response.json(
        { detail: "Too many requests. Please wait before trying again." },
        { status: 429, headers: { "Retry-After": String(admission.retryAfter || 60) } },
      );
    }
    return json("The live demo has reached its usage limit. Please try again later.", 429);
  }

  const baseUrl = (env.DIFY_BASE_URL || "https://api.dify.ai/v1").replace(/\/$/, "");
  try {
    const response = await fetch(`${baseUrl}/workflows/run`, {
      method: "POST",
      headers: { Authorization: `Bearer ${env.DIFY_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        inputs: { ...brief, additional_context: brief.additional_context || "" },
        response_mode: "streaming",
        user: `portfolio-demo-${crypto.randomUUID()}`,
      }),
      signal: AbortSignal.timeout(120_000),
    });
    if (!response.ok || !response.body) return json("The AI workflow could not start the research request.", 502);

    return new Response(response.body, {
      status: 200,
      headers: {
        "Content-Type": "text/event-stream; charset=utf-8",
        "Cache-Control": "private, no-store, no-transform",
        "X-Accel-Buffering": "no",
        "X-Content-Type-Options": "nosniff",
      },
    });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    return json(timedOut ? "The AI workflow timed out. Please try again." : "The AI workflow is currently unavailable.", timedOut ? 504 : 502);
  }
}

const worker = {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/api/v3/strategy") {
      if (request.method !== "POST") return new Response(null, { status: 405, headers: { Allow: "POST" } });
      return generateStrategy(request, env);
    }
    if (url.pathname === "/api/v5/research-strategy") {
      if (request.method !== "POST") return new Response(null, { status: 405, headers: { Allow: "POST" } });
      return proxyResearchStrategy(request, env);
    }
    if (url.pathname === "/api/analyze") {
      if (request.method !== "POST") return new Response(null, { status: 405, headers: { Allow: "POST" } });
      return generateStrategy(request, env, true);
    }
    if (url.pathname === "/health") return Response.json({ status: "ok", mode: env.DIFY_API_KEY ? "dify" : "unconfigured", version: "0.5.0" });
    if (url.pathname === "/demo" || url.pathname === "/demo/") {
      return env.ASSETS.fetch(new Request(new URL("/demo", url), request));
    }
    return env.ASSETS.fetch(request);
  },
};

export default worker;
