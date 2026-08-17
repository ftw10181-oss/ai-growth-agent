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
    }>;
    pain_points: InsightItem[];
    purchase_motivations: InsightItem[];
    adoption_barriers: InsightItem[];
    typical_scenarios: InsightItem[];
    research_questions: string[];
    assumptions_to_validate: string[];
    confidence: "low" | "medium" | "high";
  };
}
