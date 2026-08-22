export type BusinessGoal =
  | "Brand Awareness"
  | "User Acquisition"
  | "Conversion"
  | "Community Growth"
  | "Product Launch"
  | "Retention";

export interface GrowthBrief {
  product: string;
  product_description: string;
  target_market: string;
  target_audience: string;
  business_goal: BusinessGoal;
  additional_context: string;
}

export interface InsightEvidence {
  basis: "explicit_brief" | "contextual_inference" | "behavioral_hypothesis";
  confidence: "low" | "medium" | "high";
  validation_status: "brief_supported" | "needs_validation";
}

export interface InsightItem {
  insight: string;
  why_it_matters: string;
  decision_relevance: "primary" | "secondary";
  evidence: InsightEvidence;
}

export interface TraceableItem {
  source_refs: string[];
  evidence?: InsightEvidence;
}

export interface StrategyQualityReview {
  status: "passed" | "passed_with_notes" | "review_required";
  issue_count: number;
  blocking_issue_count: number;
  auto_revision_count: number;
  checks: Array<{
    code: string;
    label: string;
    status: "passed" | "warning";
    detail: string;
  }>;
  issues: Array<{
    code: string;
    path: string;
    message: string;
    severity: "low" | "medium" | "high";
    blocking: boolean;
  }>;
}

export interface StrategyResponse {
  request_id: string;
  mode: "mock" | "dify";
  strategy_summary: {
    primary_user: string;
    growth_wedge: string;
    primary_value: string;
    biggest_risk: string;
  };
  context: {
    brief_summary: string;
    product_category: string;
    target_market: string;
    target_audience: string;
    growth_stage: string;
    primary_goal: BusinessGoal;
    known_constraints: string[];
    channel_signals: string[];
    assumptions: string[];
    ambiguities: string[];
  };
  user_insight: {
    target_user: { primary_segment: string; rationale: string };
    jobs_to_be_done: Array<{
      job: string;
      dimension: "functional" | "emotional" | "social";
      why_it_matters: string;
      decision_relevance: "primary" | "secondary";
      evidence: InsightEvidence;
    }>;
    pain_points: InsightItem[];
    purchase_motivations: InsightItem[];
    adoption_barriers: InsightItem[];
    typical_scenarios: InsightItem[];
    research_questions: string[];
    assumptions_to_validate: string[];
    confidence: "low" | "medium" | "high";
  };
  market_hypothesis: {
    opportunity_statement: TraceableItem & { hypothesis: string; why_now: string; evidence: InsightEvidence };
    current_alternatives: Array<TraceableItem & { alternative: string; limitation_hypothesis: string; evidence: InsightEvidence }>;
    behavior_hypotheses: Array<TraceableItem & { hypothesis: string; trigger: string; expected_observation: string; priority: "critical" | "important" | "exploratory"; evidence: InsightEvidence }>;
    growth_wedge: TraceableItem & { segment: string; entry_scenario: string; rationale: string; evidence: InsightEvidence };
    competitive_frame: TraceableItem & { compared_with: string[]; differentiation_hypothesis: string; less_suitable_for: string; evidence: InsightEvidence };
    main_risks: Array<TraceableItem & { risk: string; consequence: string; priority: "critical" | "important" | "exploratory"; evidence: InsightEvidence }>;
    validation_priorities: Array<TraceableItem & { hypothesis_to_test: string; method: string; pass_signal: string; fail_signal: string; priority: "critical" | "important" | "exploratory" }>;
    confidence: "low" | "medium" | "high";
  };
  value_proposition: {
    primary_value: TraceableItem & { statement: string; value_type: "functional" | "emotional" | "social"; rationale: string; evidence: InsightEvidence };
    functional_values: Array<TraceableItem & { statement: string; why_it_matters: string; evidence: InsightEvidence }>;
    emotional_values: Array<TraceableItem & { statement: string; why_it_matters: string; evidence: InsightEvidence }>;
    social_values: Array<TraceableItem & { statement: string; why_it_matters: string; evidence: InsightEvidence }>;
    positioning_statement: string;
    reasons_to_believe: Array<TraceableItem & { capability: string; support_status: "brief_supported" | "needs_confirmation" }>;
    message_pillars: Array<TraceableItem & { name: string; message: string; user_problem: string; priority: "primary" | "secondary"; evidence: InsightEvidence }>;
    objections: Array<TraceableItem & { objection: string; response_hypothesis: string; evidence: InsightEvidence }>;
    message_tests: Array<TraceableItem & { angle: string; variant_a: string; variant_b: string; primary_metric: string; expected_learning: string }>;
    confidence: "low" | "medium" | "high";
  };
  quality_review: StrategyQualityReview;
}

export interface InsightResponse {
  request_id: string;
  mode: "mock" | "dify";
  context: StrategyResponse["context"];
  user_insight: StrategyResponse["user_insight"];
  quality_review?: StrategyQualityReview;
}
