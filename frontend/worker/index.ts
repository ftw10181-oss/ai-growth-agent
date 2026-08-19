interface AssetsBinding {
  fetch(request: Request): Promise<Response>;
}

interface Env {
  ASSETS: AssetsBinding;
  DIFY_API_KEY?: string;
  DIFY_BASE_URL?: string;
  LIVE_DAILY_LIMIT?: string;
  LIVE_PER_VISITOR_DAILY_LIMIT?: string;
  LIVE_MIN_INTERVAL_SECONDS?: string;
  LIVE_CACHE_TTL_SECONDS?: string;
  LIVE_FALLBACK_TO_MOCK?: string;
}

interface VisitorUsage {
  count: number;
  lastRequestAt: number;
}

interface CachedResult {
  expiresAt: number;
  body: Record<string, unknown>;
}

let usageDay = new Date().toISOString().slice(0, 10);
let globalLiveCount = 0;
const visitorUsage = new Map<string, VisitorUsage>();
const resultCache = new Map<string, CachedResult>();

const BUSINESS_GOALS = new Set([
  "Brand Awareness",
  "User Acquisition",
  "Conversion",
  "Community Growth",
  "Product Launch",
  "Retention",
]);

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isValidBrief(value: unknown): value is Record<string, string> {
  if (!isRecord(value)) return false;
  const required = [
    "product",
    "product_description",
    "target_market",
    "target_audience",
    "business_goal",
  ];
  return (
    required.every((key) => typeof value[key] === "string" && value[key].trim()) &&
    BUSINESS_GOALS.has(String(value.business_goal)) &&
    (value.additional_context === undefined || typeof value.additional_context === "string")
  );
}

function parseOutput(value: unknown): unknown {
  if (typeof value !== "string") return value;
  return JSON.parse(value);
}

interface QualityIssue {
  code: string;
  path: string;
  message: string;
}

const researchPatterns = [
  /^think about the most recent time\b/i,
  /^what do you use today\b/i,
  /^what evidence or result would you need\b/i,
];

const riskPatterns: Array<[string, RegExp]> = [
  ["unsupported_frequency", /\b(?:many|most|often|frequently|significantly)\b/i],
  ["unsupported_causality", /\b(?:leads? to|results? in|directly impacts?|improves?|increases?|decreases?|enhances?|faster|better)\b/i],
];
const hypothesisMarkers = /\b(?:hypothesis to test|may|could)\b/i;
const insightSections = ["jobs_to_be_done", "pain_points", "purchase_motivations", "adoption_barriers", "typical_scenarios"];
const sectionMinimums: Record<string, number> = {
  jobs_to_be_done: 3,
  pain_points: 2,
  purchase_motivations: 2,
  adoption_barriers: 2,
  typical_scenarios: 2,
};

function normalizeClaimLanguage(value: unknown): { insight: unknown; revisionCount: number } {
  const insight = isRecord(value) ? JSON.parse(JSON.stringify(value)) as Record<string, unknown> : value;
  if (!isRecord(insight)) return { insight, revisionCount: 0 };
  let revisionCount = 0;

  const reframe = (text: string): string => {
    const hasRisk = riskPatterns.some(([, pattern]) => pattern.test(text));
    if (hasRisk && !hypothesisMarkers.test(text)) {
      revisionCount += 1;
      return `Hypothesis to test — ${text}`;
    }
    return text;
  };

  if (isRecord(insight.target_user) && typeof insight.target_user.rationale === "string") {
    insight.target_user.rationale = reframe(insight.target_user.rationale);
  }
  insightSections.forEach((section) => {
    const items = Array.isArray(insight[section]) ? insight[section] as unknown[] : [];
    items.forEach((item) => {
      if (!isRecord(item)) return;
      const contentKey = section === "jobs_to_be_done" ? "job" : "insight";
      if (typeof item[contentKey] === "string") item[contentKey] = reframe(item[contentKey] as string);
      if (typeof item.why_it_matters === "string") item.why_it_matters = reframe(item.why_it_matters);
    });
  });
  return { insight, revisionCount };
}

function evaluateQuality(value: unknown, autoRevisionCount = 0) {
  const insight = isRecord(value) ? value : {};
  const issues: QualityIssue[] = [];

  const sectionsPassed = insightSections.every((section) => {
    const items = insight[section];
    return Array.isArray(items) && items.length >= sectionMinimums[section] && items.length <= 5 && items.some((item) => isRecord(item) && item.decision_relevance === "primary");
  });
  const jobs = Array.isArray(insight.jobs_to_be_done) ? insight.jobs_to_be_done : [];
  const jobDimensions = new Set(jobs.flatMap((item) => isRecord(item) && typeof item.dimension === "string" ? [item.dimension] : []));
  const questionsForStructure = Array.isArray(insight.research_questions) ? insight.research_questions : [];
  const assumptions = Array.isArray(insight.assumptions_to_validate) ? insight.assumptions_to_validate : [];
  const structurePassed = sectionsPassed
    && ["functional", "emotional", "social"].every((dimension) => jobDimensions.has(dimension))
    && questionsForStructure.length >= 3 && questionsForStructure.length <= 5
    && assumptions.length >= 1 && assumptions.length <= 8;
  if (!structurePassed) {
    issues.push({ code: "structure_contract", path: "user_insight", message: "A required section, item count, or primary priority needs review." });
  }

  const allItems = insightSections.flatMap((section) => Array.isArray(insight[section]) ? insight[section] as unknown[] : []);
  const evidencePassed = allItems.length > 0 && allItems.every((item) => {
    if (!isRecord(item) || !isRecord(item.evidence)) return false;
    const { basis, confidence, validation_status: status } = item.evidence;
    if (basis === "explicit_brief") return status === "brief_supported";
    if (basis === "contextual_inference" || basis === "behavioral_hypothesis") {
      return status === "needs_validation" && confidence !== "high";
    }
    return false;
  });
  if (!evidencePassed) {
    issues.push({ code: "evidence_contract", path: "user_insight", message: "Evidence basis, confidence, or validation status is inconsistent." });
  }

  const questions = Array.isArray(insight.research_questions) ? insight.research_questions : [];
  researchPatterns.forEach((pattern, index) => {
    if (typeof questions[index] !== "string" || !pattern.test(questions[index] as string)) {
      issues.push({
        code: "research_question_pattern",
        path: `research_questions.${index}`,
        message: `Rewrite this question using the required behavior-first pattern for position ${index + 1}.`,
      });
    }
  });

  const reviewable: Array<[string, string]> = [];
  if (isRecord(insight.target_user)) {
    for (const key of ["primary_segment", "rationale"]) {
      if (typeof insight.target_user[key] === "string") reviewable.push([`target_user.${key}`, insight.target_user[key] as string]);
    }
  }
  insightSections.forEach((section) => {
    const items = Array.isArray(insight[section]) ? insight[section] as unknown[] : [];
    items.forEach((item, index) => {
      if (!isRecord(item)) return;
      const contentKey = section === "jobs_to_be_done" ? "job" : "insight";
      for (const key of [contentKey, "why_it_matters"]) {
        if (typeof item[key] === "string") reviewable.push([`${section}.${index}.${key}`, item[key] as string]);
      }
    });
  });
  reviewable.forEach(([path, text]) => {
    riskPatterns.forEach(([code, pattern]) => {
      if (pattern.test(text) && !hypothesisMarkers.test(text)) {
        issues.push({ code, path, message: "Review unsupported frequency, comparative, or causal wording; use neutral or explicit hypothesis language." });
      }
    });
  });

  const researchIssueCount = issues.filter((issue) => issue.code === "research_question_pattern").length;
  const wordingIssueCount = issues.filter((issue) => issue.code.startsWith("unsupported_")).length;
  const checks = [
    { code: "structure_contract", label: "Structure contract", status: structurePassed ? "passed" : "warning", detail: structurePassed ? "Required sections, item counts, and primary priorities passed." : "A structural requirement needs review." },
    { code: "evidence_contract", label: "Evidence contract", status: evidencePassed ? "passed" : "warning", detail: evidencePassed ? "Evidence basis, confidence, and validation status are consistent." : "An evidence rule needs review." },
    { code: "research_question_patterns", label: "Research question patterns", status: researchIssueCount ? "warning" : "passed", detail: researchIssueCount ? `${researchIssueCount} behavior-first question pattern(s) need review.` : "Recent behavior, workaround, and proof threshold are covered." },
    { code: "claim_language", label: "Claim language", status: wordingIssueCount ? "warning" : "passed", detail: wordingIssueCount ? `${wordingIssueCount} potentially unsupported phrase(s) need human review.` : autoRevisionCount ? `${autoRevisionCount} high-risk phrase(s) were reframed as explicit hypotheses before this check.` : "No unsupported frequency, comparative, or causal phrasing was detected." },
  ];
  const hardIssue = issues.some((issue) => issue.code === "structure_contract" || issue.code === "evidence_contract");
  const status = hardIssue ? "review_required" : issues.length ? "passed_with_notes" : "passed";
  return { status, issue_count: issues.length, auto_revision_count: autoRevisionCount, checks, issues };
}

function boundedNumber(value: string | undefined, fallback: number, maximum: number): number {
  if (value === undefined || value.trim() === "") return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.min(maximum, Math.max(0, parsed)) : fallback;
}

function settingEnabled(value: string | undefined, fallback = true): boolean {
  if (value === undefined) return fallback;
  return !["0", "false", "no", "off"].includes(value.trim().toLowerCase());
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

function buildMockResponse(brief: Record<string, string>): Record<string, unknown> {
  const evidence = {
    basis: "contextual_inference",
    confidence: "medium",
    validation_status: "needs_validation",
  };
  const behavioralEvidence = {
    basis: "behavioral_hypothesis",
    confidence: "low",
    validation_status: "needs_validation",
  };
  const insightItem = (insight: string, whyItMatters: string, secondary = false) => ({
    insight,
    why_it_matters: whyItMatters,
    decision_relevance: secondary ? "secondary" : "primary",
    evidence: secondary ? behavioralEvidence : evidence,
  });
  const jobItem = (job: string, dimension: string, whyItMatters: string) => ({
    job,
    dimension,
    why_it_matters: whyItMatters,
    decision_relevance: dimension === "social" ? "secondary" : "primary",
    evidence: dimension === "functional" ? evidence : behavioralEvidence,
  });
  const userInsight = {
    target_user: {
      primary_segment: `${brief.target_market} ${brief.target_audience}`,
      rationale: `This segment is the starting hypothesis for testing demand for ${brief.product}.`,
    },
    jobs_to_be_done: [
      jobItem(`When I face the problem described by ${brief.product}, I want a faster way to make progress.`, "functional", "The core workflow should prove practical value quickly."),
      jobItem("When I try a new AI product, I want confidence that its recommendations are grounded.", "emotional", "Trust can determine whether a user completes a first run."),
      jobItem("When I share the result with colleagues, I want it to look credible and actionable.", "social", "Shareability may support organic acquisition."),
    ],
    pain_points: [
      insightItem("Users may spend too much time turning scattered information into a clear decision.", "Time-to-insight is a testable activation metric."),
      insightItem("Generic AI output may feel difficult to trust or apply.", "The product should expose assumptions and validation needs."),
      insightItem("A new workflow may feel like extra work before its value is visible.", "The first-run experience should minimize setup friction.", true),
    ],
    purchase_motivations: [
      insightItem(`A near-term ${brief.business_goal.toLowerCase()} decision may create urgency.`, "A concrete decision moment can anchor acquisition messaging."),
      insightItem("A structured report may reduce the effort needed to align a team.", "Reusable outputs can strengthen perceived value."),
      insightItem("A low-risk trial can help users compare the workflow with their current process.", "Experiential proof can reduce adoption uncertainty.", true),
    ],
    adoption_barriers: [
      insightItem("Users may question whether the analysis reflects real customer evidence.", "Clear evidence labels and research prompts are essential."),
      insightItem("Sensitive business inputs may create privacy concerns.", "Data-handling expectations should be explicit."),
      insightItem("The suggested actions may not fit every market or growth stage.", "Users need a clear way to refine context.", true),
    ],
    typical_scenarios: [
      insightItem("A growth operator needs to prepare an initial market or user hypothesis before research.", "This is a clear pre-research use case."),
      insightItem("A small team needs a shared starting point for deciding what to test next.", "A structured result can support prioritization."),
      insightItem("A founder wants to turn an early product brief into interview questions.", "Research-question generation creates an actionable handoff.", true),
    ],
    research_questions: [
      "Think about the most recent time you faced this growth problem. What happened?",
      "What do you use today to make this decision, and where does it fall short?",
      "What evidence or result would you need before trusting an AI-generated recommendation?",
      "Which part of this workflow would be unacceptable to automate?",
    ],
    assumptions_to_validate: [
      `${brief.target_audience} experiences this problem often enough to seek a dedicated workflow.`,
      `The proposed value is relevant to the ${brief.target_market} market.`,
    ],
    confidence: "medium",
  };
  return {
    request_id: crypto.randomUUID(),
    mode: "mock",
    context: {
      brief_summary: `${brief.product} is being explored for ${brief.target_audience} in ${brief.target_market}, with ${brief.business_goal} as the immediate goal.`,
      product_category: "AI-enabled growth workflow",
      target_market: brief.target_market,
      target_audience: brief.target_audience,
      growth_stage: "unknown",
      primary_goal: brief.business_goal,
      known_constraints: [],
      channel_signals: [],
      assumptions: userInsight.assumptions_to_validate,
      ambiguities: ["These outputs are hypotheses and require customer or market validation."],
    },
    user_insight: userInsight,
    quality_review: evaluateQuality(userInsight),
  };
}

function mockResponse(brief: Record<string, string>, reason: string): Response {
  return Response.json(buildMockResponse(brief), {
    headers: {
      "X-AI-Fallback": reason,
      "Cache-Control": "no-store",
    },
  });
}

async function visitorId(request: Request): Promise<string> {
  const forwarded = request.headers.get("CF-Connecting-IP")
    || request.headers.get("X-Forwarded-For")?.split(",", 1)[0].trim()
    || "anonymous";
  return digest(forwarded);
}

async function cacheKey(brief: Record<string, string>): Promise<string> {
  const normalized = JSON.stringify(brief, Object.keys(brief).sort());
  return digest(normalized);
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
  if (visitorLimit > 0 && usage.count >= visitorLimit) {
    return { allowed: false, reason: "visitor_daily_limit" };
  }
  const dailyLimit = boundedNumber(env.LIVE_DAILY_LIMIT, 50, 100000);
  if (dailyLimit > 0 && globalLiveCount >= dailyLimit) {
    return { allowed: false, reason: "global_daily_limit" };
  }
  usage.count += 1;
  usage.lastRequestAt = now;
  visitorUsage.set(id, usage);
  globalLiveCount += 1;
  return { allowed: true };
}

function json(detail: string, status: number): Response {
  return Response.json({ detail }, { status });
}

async function analyze(request: Request, env: Env): Promise<Response> {
  let brief: unknown;
  try {
    brief = await request.json();
  } catch {
    return json("Request body must be valid JSON.", 400);
  }
  if (!isValidBrief(brief)) {
    return json("Invalid growth brief.", 422);
  }

  if (!env.DIFY_API_KEY) {
    return mockResponse(brief, "live_service_not_configured");
  }

  const key = await cacheKey(brief);
  const cached = resultCache.get(key);
  if (cached && cached.expiresAt > Date.now()) {
    return Response.json(cached.body, {
      headers: { "X-AI-Cache": "HIT", "Cache-Control": "private, no-store" },
    });
  }
  if (cached) resultCache.delete(key);

  const admission = admitLive(await visitorId(request), env);
  if (!admission.allowed) {
    if (admission.reason === "rate_limited") {
      return Response.json(
        { detail: "Too many requests. Please wait before trying again." },
        {
          status: 429,
          headers: { "Retry-After": String(admission.retryAfter || 60) },
        },
      );
    }
    return mockResponse(brief, admission.reason || "quota_limit");
  }

  const baseUrl = (env.DIFY_BASE_URL || "https://api.dify.ai/v1").replace(/\/$/, "");
  try {
    const response = await fetch(`${baseUrl}/workflows/run`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.DIFY_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        inputs: { ...brief, additional_context: brief.additional_context || "" },
        response_mode: "blocking",
        user: `portfolio-demo-${crypto.randomUUID()}`,
      }),
      signal: AbortSignal.timeout(90_000),
    });

    if (!response.ok) {
      if (settingEnabled(env.LIVE_FALLBACK_TO_MOCK)) {
        return mockResponse(brief, `upstream_${response.status}`);
      }
      return json("The AI workflow could not complete the request.", 502);
    }
    const body = (await response.json()) as Record<string, unknown>;
    const data = isRecord(body.data) ? body.data : null;
    const outputs = data && isRecord(data.outputs) ? data.outputs : null;
    if (!data || data.status !== "succeeded" || !outputs) {
      if (settingEnabled(env.LIVE_FALLBACK_TO_MOCK)) {
        return mockResponse(brief, "upstream_invalid_response");
      }
      return json("The AI workflow returned an unexpected response.", 502);
    }

    const rawUserInsight = parseOutput(outputs.user_insight);
    const { insight: userInsight, revisionCount } = normalizeClaimLanguage(rawUserInsight);
    const result = {
      request_id: String(body.workflow_run_id || body.task_id || crypto.randomUUID()),
      mode: "dify",
      context: parseOutput(outputs.context),
      user_insight: userInsight,
      quality_review: evaluateQuality(userInsight, revisionCount),
    };
    const cacheTtlSeconds = boundedNumber(env.LIVE_CACHE_TTL_SECONDS, 86400, 604800);
    if (cacheTtlSeconds > 0) {
      resultCache.set(key, { expiresAt: Date.now() + cacheTtlSeconds * 1000, body: result });
    }
    return Response.json(result, {
      headers: { "X-AI-Cache": "MISS", "Cache-Control": "private, no-store" },
    });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
    if (settingEnabled(env.LIVE_FALLBACK_TO_MOCK)) {
      return mockResponse(brief, timedOut ? "upstream_timeout" : "upstream_error");
    }
    return json(
      timedOut ? "The AI workflow timed out. Please try again." : "The AI workflow is currently unavailable.",
      timedOut ? 504 : 502,
    );
  }
}

const worker = {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname === "/api/analyze") {
      if (request.method !== "POST") {
        return new Response(null, { status: 405, headers: { Allow: "POST" } });
      }
      return analyze(request, env);
    }
    if (url.pathname === "/health") {
      return Response.json({
        status: "ok",
        mode: env.DIFY_API_KEY ? "dify" : "unconfigured",
        version: "0.2.1",
      });
    }
    // Map the pretty demo path to the built demo.html asset.
    if (url.pathname === "/demo" || url.pathname === "/demo/") {
      return env.ASSETS.fetch(new Request(new URL("/demo.html", url), request));
    }
    return env.ASSETS.fetch(request);
  },
};

export default worker;
