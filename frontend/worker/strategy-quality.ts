export type JsonRecord = Record<string, unknown>;

export interface StrategyIssue {
  code: string;
  path: string;
  message: string;
  severity: "low" | "medium" | "high";
  blocking: boolean;
}

const marketAssertion = /\b(?:unlike|market demand|users? prefer|customers? prefer|willingness to pay|willing to pay|existing (?:\w+\s+){0,2}(?:tools|apps|products)|(?:tools|apps|competitors?)\b.{0,40}\b(?:fail|fails|lack|lacks|cannot|can't|may not|do not|does not|are not|cause|causes))\b/i;
const unsupportedStrength = /\b(?:many|most|often|frequently|significantly|better than|worse than)\b/i;
const hypothesisMarker = /\b(?:may|might|could|hypothesis|to test)\b/i;
const measurableSignal = /(?:\d|%|percent|at least|at most|no more than|fewer than|more than|within \d)/i;

const basisRank: Record<string, number> = { behavioral_hypothesis: 1, contextual_inference: 2, explicit_brief: 3 };
const confidenceRank: Record<string, number> = { low: 1, medium: 2, high: 3 };

export function isRecord(value: unknown): value is JsonRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function* traceableItems(value: unknown, path: string): Generator<[string, JsonRecord]> {
  if (isRecord(value)) {
    if (Array.isArray(value.source_refs)) yield [path, value];
    for (const [key, child] of Object.entries(value)) yield* traceableItems(child, `${path}.${key}`);
  } else if (Array.isArray(value)) {
    for (const [index, child] of value.entries()) yield* traceableItems(child, `${path}.${index}`);
  }
}

function resolveRef(reference: string, roots: JsonRecord): { valid: boolean; evidence?: JsonRecord } {
  const parts = reference.split(".");
  let current: unknown = roots[parts[0]];
  if (current === undefined) return { valid: false };
  let evidence: JsonRecord | undefined;
  for (const part of parts.slice(1)) {
    if (isRecord(current) && isRecord(current.evidence)) evidence = current.evidence;
    if (isRecord(current) && part in current) current = current[part];
    else if (Array.isArray(current) && /^\d+$/.test(part) && Number(part) < current.length) current = current[Number(part)];
    else return { valid: false };
  }
  if (isRecord(current) && isRecord(current.evidence)) evidence = current.evidence;
  if (parts[0] === "context" && !evidence) {
    const inferred = ["product_category", "assumptions", "ambiguities"].includes(parts[1]);
    evidence = { basis: inferred ? "contextual_inference" : "explicit_brief", confidence: inferred ? "medium" : "high" };
  }
  return { valid: true, evidence };
}

function itemText(item: JsonRecord): string {
  const ignored = new Set(["source_refs", "evidence", "priority", "support_status"]);
  return Object.entries(item).flatMap(([key, value]) => !ignored.has(key) && typeof value === "string" ? [value] : []).join(" ");
}

export function normalizeStrategyClaims(marketValue: unknown, propositionValue: unknown) {
  const market = clone(marketValue);
  const value = clone(propositionValue);
  let revisionCount = 0;
  for (const [root, payload] of [["market_hypothesis", market], ["value_proposition", value]] as const) {
    for (const [, item] of traceableItems(payload, root)) {
      if (!isRecord(item.evidence) || item.evidence.basis === "explicit_brief") continue;
      for (const [key, content] of Object.entries(item)) {
        if (["source_refs", "evidence", "priority", "support_status"].includes(key) || typeof content !== "string") continue;
        if (!hypothesisMarker.test(content) && (marketAssertion.test(content) || unsupportedStrength.test(content))) {
          item[key] = `Hypothesis to test — ${content}`;
          revisionCount += 1;
        }
      }
    }
  }
  return { market, value, revisionCount };
}

export function evaluateStrategyQuality(
  brief: JsonRecord,
  context: unknown,
  userInsight: unknown,
  market: unknown,
  value: unknown,
  autoRevisionCount = 0,
) {
  const contextData = isRecord(context) ? context : {};
  const userData = isRecord(userInsight) ? userInsight : {};
  const marketData = isRecord(market) ? market : {};
  const valueData = isRecord(value) ? value : {};
  const roots: JsonRecord = { context: contextData, user_insight: userData, market_hypothesis: marketData };
  const issues: StrategyIssue[] = [];

  const requiredMarketArrays = ["current_alternatives", "behavior_hypotheses", "main_risks", "validation_priorities"];
  const requiredValueArrays = ["functional_values", "emotional_values", "social_values", "reasons_to_believe", "message_pillars", "objections", "message_tests"];
  const structurePassed = ["opportunity_statement", "growth_wedge", "competitive_frame"].every((key) => isRecord(marketData[key]))
    && requiredMarketArrays.every((key) => Array.isArray(marketData[key]) && (marketData[key] as unknown[]).length > 0)
    && isRecord(valueData.primary_value)
    && requiredValueArrays.every((key) => Array.isArray(valueData[key]) && (valueData[key] as unknown[]).length > 0);
  if (!structurePassed) issues.push({ code: "structure_contract", path: "strategy", message: "A required V0.3 strategy module or collection is missing.", severity: "high", blocking: true });

  const traceable = [
    ...traceableItems(marketData, "market_hypothesis"),
    ...traceableItems(valueData, "value_proposition"),
  ];
  let referenceIssues = 0;
  let evidenceIssues = 0;
  let claimIssues = 0;
  for (const [path, item] of traceable) {
    const allowedRoots = path.startsWith("market_hypothesis") ? new Set(["context", "user_insight"]) : new Set(["context", "user_insight", "market_hypothesis"]);
    const upstreamEvidence: JsonRecord[] = [];
    for (const ref of (item.source_refs as unknown[]).filter((candidate): candidate is string => typeof candidate === "string")) {
      const root = ref.split(".", 1)[0];
      const resolved = resolveRef(ref, roots);
      if (!allowedRoots.has(root) || !resolved.valid) {
        referenceIssues += 1;
        issues.push({ code: "invalid_source_ref", path: `${path}.source_refs`, message: `${ref} does not resolve to an allowed upstream field.`, severity: "high", blocking: true });
      } else if (resolved.evidence) upstreamEvidence.push(resolved.evidence);
    }
    if (isRecord(item.evidence) && upstreamEvidence.length) {
      const downstreamBasis = basisRank[String(item.evidence.basis)] ?? 0;
      const downstreamConfidence = confidenceRank[String(item.evidence.confidence)] ?? 0;
      const weakestBasis = Math.min(...upstreamEvidence.map((evidence) => basisRank[String(evidence.basis)] ?? 0));
      const weakestConfidence = Math.min(...upstreamEvidence.map((evidence) => confidenceRank[String(evidence.confidence)] ?? 0));
      if (downstreamBasis > weakestBasis || downstreamConfidence > weakestConfidence) {
        evidenceIssues += 1;
        issues.push({ code: "evidence_stronger_than_source", path: `${path}.evidence`, message: "Downstream evidence is stronger than at least one cited source.", severity: "high", blocking: true });
      }
    }
    if (isRecord(item.evidence)) {
      const text = itemText(item);
      const risky = marketAssertion.test(text) || unsupportedStrength.test(text);
      if (item.evidence.basis === "explicit_brief" && risky) {
        claimIssues += 1;
        issues.push({ code: "unsupported_explicit_market_claim", path, message: "A factual market or comparative claim is not established by the submitted brief.", severity: "high", blocking: true });
      } else if (risky && !hypothesisMarker.test(text)) {
        claimIssues += 1;
        issues.push({ code: "unsupported_claim_language", path, message: "Use neutral or explicit hypothesis language for this market claim.", severity: "medium", blocking: false });
      }
    }
  }

  let continuityIssues = 0;
  const primaryValue = isRecord(valueData.primary_value) ? valueData.primary_value : {};
  const primaryRefs = Array.isArray(primaryValue.source_refs) ? primaryValue.source_refs.filter((ref): ref is string => typeof ref === "string") : [];
  const primaryRoots = new Set(primaryRefs.map((ref) => ref.split(".", 1)[0]));
  if (!primaryRoots.has("user_insight") || !primaryRoots.has("market_hypothesis")) {
    continuityIssues += 1;
    issues.push({ code: "primary_value_missing_decision_link", path: "value_proposition.primary_value.source_refs", message: "Primary value must cite both a user insight and a market hypothesis.", severity: "high", blocking: true });
  }
  if (contextData.primary_goal !== brief.business_goal) {
    continuityIssues += 1;
    issues.push({ code: "business_goal_drift", path: "context.primary_goal", message: "The normalized business goal differs from the submitted brief.", severity: "high", blocking: true });
  }

  let testabilityIssues = 0;
  const priorities = Array.isArray(marketData.validation_priorities) ? marketData.validation_priorities : [];
  priorities.forEach((priority, index) => {
    if (!isRecord(priority) || typeof priority.pass_signal !== "string" || typeof priority.fail_signal !== "string" || !measurableSignal.test(priority.pass_signal) || !measurableSignal.test(priority.fail_signal)) {
      testabilityIssues += 1;
      issues.push({ code: "validation_signal_not_measurable", path: `market_hypothesis.validation_priorities.${index}`, message: "Pass and fail signals need an observable threshold, count, percentage, or time bound.", severity: "medium", blocking: false });
    }
  });

  const checks = [
    { code: "structure_contract", label: "Structure contract", status: structurePassed ? "passed" : "warning", detail: structurePassed ? "All four strategy objects passed the V0.3 contract." : "A required strategy object needs review." },
    { code: "reference_integrity", label: "Reference integrity", status: referenceIssues ? "warning" : "passed", detail: referenceIssues ? `${referenceIssues} invalid source reference(s) found.` : "Every source reference resolves to an allowed upstream field." },
    { code: "evidence_inheritance", label: "Evidence inheritance", status: evidenceIssues ? "warning" : "passed", detail: evidenceIssues ? `${evidenceIssues} item(s) overstate upstream evidence.` : "Downstream evidence does not exceed its weakest source." },
    { code: "market_claim_grounding", label: "Market claim grounding", status: claimIssues ? "warning" : "passed", detail: claimIssues ? `${claimIssues} market claim(s) need review.` : autoRevisionCount ? `${autoRevisionCount} inferred claim(s) were reframed before this check.` : "No unsupported factual market claims were detected." },
    { code: "decision_continuity", label: "Decision continuity", status: continuityIssues ? "warning" : "passed", detail: continuityIssues ? `${continuityIssues} upstream decision link(s) need review.` : "Goal, user insight, market hypothesis, and primary value remain connected." },
    { code: "validation_testability", label: "Validation testability", status: testabilityIssues ? "warning" : "passed", detail: testabilityIssues ? `${testabilityIssues} validation plan(s) need measurable signals.` : "Every validation priority has measurable pass and fail signals." },
  ] as Array<{ code: string; label: string; status: "passed" | "warning"; detail: string }>;
  const blockingCount = issues.filter((issue) => issue.blocking).length;
  return {
    status: blockingCount ? "review_required" : issues.length ? "passed_with_notes" : "passed",
    issue_count: issues.length,
    blocking_issue_count: blockingCount,
    auto_revision_count: autoRevisionCount,
    checks,
    issues,
  };
}
