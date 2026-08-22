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

export type ResearchStatus = "complete" | "partial" | "unavailable" | "offline_fixture";
export type ResearchDimension =
  | "user_behavior"
  | "market_context"
  | "competitor"
  | "channel"
  | "risk"
  | "product_expectation";

export interface ResearchQuestion {
  question_id: string;
  question: string;
  dimension: ResearchDimension;
  decision_impact: string;
  evidence_needed: string;
  query: string;
  recency_preference: "last_12_months" | "last_24_months" | "any";
  priority: "critical" | "important" | "exploratory";
}

export interface ResearchSource {
  source_id: string;
  title: string;
  url: string;
  domain: string;
  publisher: string | null;
  published_at: string | null;
  retrieved_at: string;
  query_ids: string[];
  source_class: "primary" | "independent_secondary" | "vendor" | "community" | "unknown";
  relevance_score: number;
  freshness: "current" | "dated" | "unknown";
  snippet: string;
  limitations: string[];
}

export interface EvidenceFinding {
  finding_id: string;
  research_question_ids: string[];
  claim: string;
  dimension: ResearchDimension;
  status: "supported" | "contested" | "insufficient";
  supporting_source_ids: string[];
  contradicting_source_ids: string[];
  confidence: "low" | "medium" | "high";
  implication: string;
  limitations: string[];
}

export interface ResearchStrategyResponse extends StrategyResponse {
  research_status: ResearchStatus;
  researched_at: string;
  research_plan: {
    decision_context: string;
    questions: ResearchQuestion[];
    search_limits: {
      max_queries: 5;
      max_results_per_query: number;
      max_retained_sources: 10;
    };
  };
  source_manifest: {
    research_status: ResearchStatus;
    researched_at: string;
    sources: ResearchSource[];
    failed_query_ids: string[];
  };
  evidence_brief: {
    summary: string;
    findings: EvidenceFinding[];
    research_gaps: Array<{
      gap: string;
      decision_risk: string;
      next_step: string;
      priority: "critical" | "important" | "exploratory";
    }>;
    source_coverage: {
      retained_source_count: number;
      question_count: number;
      answered_question_count: number;
      source_diversity_note: string;
    };
  };
  evidence_audit: {
    status: "passed" | "passed_with_notes";
    issue_count: number;
    issues: Array<{ code: string; path: string; message: string }>;
    minimum_relevance: number;
  };
  claim_citations: {
    citations: Array<{
      claim_path: string;
      finding_ids: string[];
      claim_status: "evidence_backed" | "contested" | "inference" | "unknown";
      explanation: string;
    }>;
  };
  research_summary: {
    evidence_coverage: string;
    largest_research_gap: string;
  };
  research_quality_review: StrategyQualityReview;
}
