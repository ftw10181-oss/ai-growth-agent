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

export interface InsightItem {
  insight: string;
  why_it_matters: string;
  decision_relevance?: "primary" | "secondary";
  evidence?: InsightEvidence;
}

export interface InsightEvidence {
  basis: "explicit_brief" | "contextual_inference" | "behavioral_hypothesis";
  confidence: "low" | "medium" | "high";
  validation_status: "brief_supported" | "needs_validation";
}

export interface QualityReview {
  status: "passed" | "review_required";
  issue_count: number;
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
  }>;
}

export interface InsightResponse {
  request_id: string;
  mode: string;
  context: {
    brief_summary: string;
    assumptions: string[];
    ambiguities: string[];
    primary_goal: BusinessGoal;
  };
  user_insight: {
    target_user: { primary_segment: string; rationale: string };
    jobs_to_be_done: Array<{
      job: string;
      dimension: "functional" | "emotional" | "social";
      why_it_matters: string;
      decision_relevance?: "primary" | "secondary";
      evidence?: InsightEvidence;
    }>;
    pain_points: InsightItem[];
    purchase_motivations: InsightItem[];
    adoption_barriers: InsightItem[];
    typical_scenarios: InsightItem[];
    research_questions: string[];
    assumptions_to_validate: string[];
    confidence: "low" | "medium" | "high";
  };
  quality_review?: QualityReview;
}
