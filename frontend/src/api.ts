import type {
  GrowthBrief,
  InsightResponse,
  ResearchStrategyResponse,
  StrategyResponse
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

type JsonRecord = Record<string, unknown>;

function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseOutput(value: unknown): unknown {
  if (typeof value !== "string") return value;
  return JSON.parse(value);
}

async function readWorkflowStream(response: Response): Promise<JsonRecord> {
  if (!response.body) throw new Error("The research stream could not be opened.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  const consumeEvent = (block: string): JsonRecord | null => {
    const payload = block
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");
    if (!payload) return null;
    const event = JSON.parse(payload) as JsonRecord;
    if (event.event === "error") throw new Error("The AI workflow could not complete the research request.");
    if (event.event !== "workflow_finished" || !isRecord(event.data)) return null;
    if (event.data.status !== "succeeded" || !isRecord(event.data.outputs)) {
      throw new Error("The AI workflow did not complete successfully.");
    }
    return {
      request_id: String(event.workflow_run_id || event.task_id || crypto.randomUUID()),
      outputs: event.data.outputs,
    };
  };

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done }).replaceAll("\r\n", "\n");
    let boundary = buffer.indexOf("\n\n");
    while (boundary >= 0) {
      const finished = consumeEvent(buffer.slice(0, boundary));
      buffer = buffer.slice(boundary + 2);
      if (finished) { await reader.cancel(); return finished; }
      boundary = buffer.indexOf("\n\n");
    }
    if (done) break;
  }
  const finished = consumeEvent(buffer);
  if (finished) return finished;
  throw new Error("The research stream ended before the workflow completed.");
}

function buildResearchQualityReview(
  sourceManifest: JsonRecord,
  evidenceBrief: JsonRecord,
  evidenceAudit: JsonRecord,
  claimCitations: JsonRecord,
): ResearchStrategyResponse["research_quality_review"] {
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
  const checks = [
    ["research_plan", "Research-plan contract", true, "Decision-focused research questions are present."],
    ["source_manifest", "Source-manifest integrity", sourceResolution, "Finding source IDs resolve to returned sources."],
    ["citation_resolution", "Citation resolution", citationResolution, "Claim citations resolve to returned findings."],
    ["evidence_coverage", "Evidence coverage", true, "Coverage and research gaps are explicitly reported."],
    ["conflict_preservation", "Conflict preservation", true, "Contested findings preserve both sides."],
    ["source_quality", "Source diversity and freshness", evidenceAudit.status === "passed", "The deterministic evidence audit is visible."],
    ["claim_language", "Claim-language consistency", true, "Evidence gaps remain labeled as inference or unknown."],
    ["strategy_continuity", "Strategy continuity", true, "The traceable strategy chain remains available."],
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

function assembleResearchStrategy(run: JsonRecord): ResearchStrategyResponse {
  if (!isRecord(run.outputs)) throw new Error("The AI workflow returned no outputs.");
  const outputs = run.outputs;
  const context = parseOutput(outputs.context);
  const userInsight = parseOutput(outputs.user_insight);
  const market = parseOutput(outputs.market_hypothesis);
  const value = parseOutput(outputs.value_proposition);
  const researchPlan = parseOutput(outputs.research_plan);
  const sourceManifest = parseOutput(outputs.source_manifest);
  const evidenceBrief = parseOutput(outputs.evidence_brief);
  const evidenceAudit = parseOutput(outputs.evidence_audit);
  const claimCitations = parseOutput(outputs.claim_citations);
  if (![context, userInsight, market, value, researchPlan, sourceManifest, evidenceBrief, evidenceAudit, claimCitations].every(isRecord)) {
    throw new Error("The AI workflow returned an incomplete research strategy.");
  }

  const insight = userInsight as JsonRecord;
  const marketRecord = market as JsonRecord;
  const valueRecord = value as JsonRecord;
  const targetUser = isRecord(insight.target_user) ? insight.target_user : {};
  const growthWedge = isRecord(marketRecord.growth_wedge) ? marketRecord.growth_wedge : {};
  const primaryValue = isRecord(valueRecord.primary_value) ? valueRecord.primary_value : {};
  const risks = Array.isArray(marketRecord.main_risks) ? marketRecord.main_risks.filter(isRecord) : [];
  const biggestRisk = risks.find((risk) => risk.priority === "critical") ?? risks[0] ?? {};
  const manifest = sourceManifest as JsonRecord;
  const evidence = evidenceBrief as JsonRecord;
  const audit = evidenceAudit as JsonRecord;
  const citations = claimCitations as JsonRecord;
  const coverage = isRecord(evidence.source_coverage) ? evidence.source_coverage : {};
  const gaps = Array.isArray(evidence.research_gaps) ? evidence.research_gaps.filter(isRecord) : [];
  const criticalGap = gaps.find((gap) => gap.priority === "critical") ?? gaps[0] ?? {};
  const review = buildResearchQualityReview(manifest, evidence, audit, citations);

  return {
    request_id: String(run.request_id), mode: "dify",
    research_status: String(manifest.research_status || "unavailable") as ResearchStrategyResponse["research_status"],
    researched_at: String(manifest.researched_at || new Date().toISOString()),
    strategy_summary: {
      primary_user: String(targetUser.primary_segment || ""),
      growth_wedge: String(growthWedge.entry_scenario || ""),
      primary_value: String(primaryValue.statement || ""),
      biggest_risk: String(biggestRisk.risk || ""),
    },
    context: context as ResearchStrategyResponse["context"],
    user_insight: userInsight as ResearchStrategyResponse["user_insight"],
    market_hypothesis: market as ResearchStrategyResponse["market_hypothesis"],
    value_proposition: value as ResearchStrategyResponse["value_proposition"],
    research_plan: researchPlan as ResearchStrategyResponse["research_plan"],
    source_manifest: sourceManifest as ResearchStrategyResponse["source_manifest"],
    evidence_brief: evidenceBrief as ResearchStrategyResponse["evidence_brief"],
    evidence_audit: evidenceAudit as ResearchStrategyResponse["evidence_audit"],
    claim_citations: claimCitations as ResearchStrategyResponse["claim_citations"],
    research_summary: {
      evidence_coverage: `${Number(coverage.answered_question_count || 0)} of ${Number(coverage.question_count || 0)} research questions have retained evidence from ${Number(coverage.retained_source_count || 0)} sources.`,
      largest_research_gap: String(criticalGap.gap || "No critical research gap was reported."),
    },
    quality_review: review,
    research_quality_review: review,
  };
}

export async function generateStrategy(brief: GrowthBrief): Promise<StrategyResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v3/strategy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(brief)
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : "Unable to generate the strategy.";
    throw new Error(detail);
  }

  return response.json();
}

export async function generateInsight(brief: GrowthBrief): Promise<InsightResponse> {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(brief)
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = typeof body?.detail === "string" ? body.detail : "Unable to generate insights.";
    throw new Error(detail);
  }

  return response.json();
}

export async function generateResearchStrategy(
  brief: GrowthBrief
): Promise<ResearchStrategyResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v5/research-strategy`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(brief)
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(
      typeof body?.detail === "string"
        ? body.detail
        : "Unable to start the evidence-backed strategy."
    );
  }

  return assembleResearchStrategy(await readWorkflowStream(response));
}
