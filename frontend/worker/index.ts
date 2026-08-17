interface AssetsBinding {
  fetch(request: Request): Promise<Response>;
}

interface Env {
  ASSETS: AssetsBinding;
  DIFY_API_KEY?: string;
  DIFY_BASE_URL?: string;
}

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

function json(detail: string, status: number): Response {
  return Response.json({ detail }, { status });
}

async function analyze(request: Request, env: Env): Promise<Response> {
  if (!env.DIFY_API_KEY) {
    return json("Live AI service is not configured.", 503);
  }

  let brief: unknown;
  try {
    brief = await request.json();
  } catch {
    return json("Request body must be valid JSON.", 400);
  }
  if (!isValidBrief(brief)) {
    return json("Invalid growth brief.", 422);
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
      return json("The AI workflow could not complete the request.", 502);
    }
    const body = (await response.json()) as Record<string, unknown>;
    const data = isRecord(body.data) ? body.data : null;
    const outputs = data && isRecord(data.outputs) ? data.outputs : null;
    if (!data || data.status !== "succeeded" || !outputs) {
      return json("The AI workflow returned an unexpected response.", 502);
    }

    return Response.json({
      request_id: String(body.workflow_run_id || body.task_id || crypto.randomUUID()),
      mode: "dify",
      context: parseOutput(outputs.context),
      user_insight: parseOutput(outputs.user_insight),
    });
  } catch (error) {
    const timedOut = error instanceof DOMException && error.name === "TimeoutError";
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
      return Response.json({ status: "ok", mode: env.DIFY_API_KEY ? "dify" : "unconfigured" });
    }
    return env.ASSETS.fetch(request);
  },
};

export default worker;
