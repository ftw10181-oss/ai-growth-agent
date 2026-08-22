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

async function generateStrategy(request: Request, env: Env, legacyInsightOnly = false): Promise<Response> {
  if (!env.DIFY_API_KEY) return json("Live AI service is not configured.", 503);
  let brief: unknown;
  try { brief = await request.json(); }
  catch { return json("Request body must be valid JSON.", 400); }
  if (!isValidBrief(brief)) return json("Invalid growth brief.", 422);

  const key = `${legacyInsightOnly ? "insight" : "strategy"}:${await cacheKey(brief)}`;
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
      body: JSON.stringify({ inputs: { ...brief, additional_context: brief.additional_context || "" }, response_mode: "blocking", user: `portfolio-demo-${crypto.randomUUID()}` }),
      signal: AbortSignal.timeout(120_000),
    });
    if (!response.ok) return json("The AI workflow could not complete the request.", 502);
    const body = await response.json() as Record<string, unknown>;
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
    const result = legacyInsightOnly
      ? {
          request_id: fullResult.request_id,
          mode: fullResult.mode,
          context: fullResult.context,
          user_insight: fullResult.user_insight,
          quality_review: fullResult.quality_review,
        }
      : fullResult;
    const cacheTtlSeconds = boundedNumber(env.LIVE_CACHE_TTL_SECONDS, 86400, 604800);
    if (cacheTtlSeconds > 0) resultCache.set(key, { expiresAt: Date.now() + cacheTtlSeconds * 1000, body: result });
    return Response.json(result, { headers: { "X-AI-Cache": "MISS", "Cache-Control": "private, no-store" } });
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
    if (url.pathname === "/api/analyze") {
      if (request.method !== "POST") return new Response(null, { status: 405, headers: { Allow: "POST" } });
      return generateStrategy(request, env, true);
    }
    if (url.pathname === "/health") return Response.json({ status: "ok", mode: env.DIFY_API_KEY ? "dify" : "unconfigured", version: "0.3.0" });
    if (url.pathname === "/demo" || url.pathname === "/demo/") {
      return env.ASSETS.fetch(new Request(new URL("/demo", url), request));
    }
    return env.ASSETS.fetch(request);
  },
};

export default worker;
