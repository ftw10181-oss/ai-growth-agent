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

function evaluateQuality(value: unknown) {
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
    { code: "claim_language", label: "Claim language", status: wordingIssueCount ? "warning" : "passed", detail: wordingIssueCount ? `${wordingIssueCount} potentially unsupported phrase(s) need human review.` : "No unsupported frequency, comparative, or causal phrasing was detected." },
  ];
  return { status: issues.length ? "review_required" : "passed", issue_count: issues.length, checks, issues };
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

    const userInsight = parseOutput(outputs.user_insight);
    return Response.json({
      request_id: String(body.workflow_run_id || body.task_id || crypto.randomUUID()),
      mode: "dify",
      context: parseOutput(outputs.context),
      user_insight: userInsight,
      quality_review: evaluateQuality(userInsight),
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
      return Response.json({
        status: "ok",
        mode: env.DIFY_API_KEY ? "dify" : "unconfigured",
        version: "0.2.0",
      });
    }
    return env.ASSETS.fetch(request);
  },
};

export default worker;
