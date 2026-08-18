from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BusinessGoal(str, Enum):
    BRAND_AWARENESS = "Brand Awareness"
    USER_ACQUISITION = "User Acquisition"
    CONVERSION = "Conversion"
    COMMUNITY_GROWTH = "Community Growth"
    PRODUCT_LAUNCH = "Product Launch"
    RETENTION = "Retention"


class GrowthStage(str, Enum):
    NEW_MARKET_ENTRY = "new_market_entry"
    LAUNCH = "launch"
    EARLY_GROWTH = "early_growth"
    SCALING = "scaling"
    RETENTION = "retention"
    UNKNOWN = "unknown"


class GrowthBrief(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    product: str = Field(min_length=2, max_length=120)
    product_description: str = Field(min_length=20, max_length=2000)
    target_market: str = Field(min_length=2, max_length=120)
    target_audience: str = Field(min_length=5, max_length=500)
    business_goal: BusinessGoal
    additional_context: str = Field(default="", max_length=2000)


class NormalizedContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brief_summary: str
    product_category: str
    target_market: str
    target_audience: str
    growth_stage: GrowthStage
    primary_goal: BusinessGoal
    known_constraints: list[str]
    channel_signals: list[str]
    assumptions: list[str] = Field(min_length=1)
    ambiguities: list[str]


class TargetUser(BaseModel):
    primary_segment: str
    rationale: str


class JobToBeDoneV01(BaseModel):
    job: str
    dimension: Literal["functional", "emotional", "social"]
    why_it_matters: str


class InsightItemV01(BaseModel):
    insight: str
    why_it_matters: str


class UserInsightV01(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_user: TargetUser
    jobs_to_be_done: list[JobToBeDoneV01] = Field(min_length=3, max_length=5)
    pain_points: list[InsightItemV01] = Field(min_length=3, max_length=5)
    purchase_motivations: list[InsightItemV01] = Field(min_length=3, max_length=5)
    adoption_barriers: list[InsightItemV01] = Field(min_length=3, max_length=5)
    typical_scenarios: list[InsightItemV01] = Field(min_length=3, max_length=5)
    research_questions: list[str] = Field(min_length=3, max_length=5)
    assumptions_to_validate: list[str] = Field(min_length=1, max_length=8)
    confidence: str = Field(pattern="^(low|medium|high)$")

    @model_validator(mode="after")
    def require_all_job_dimensions(self):
        dimensions = {item.dimension for item in self.jobs_to_be_done}
        required = {"functional", "emotional", "social"}
        if not required.issubset(dimensions):
            raise ValueError(
                "jobs_to_be_done must include functional, emotional, and social dimensions"
            )
        return self


class UserInsightResponseV01(BaseModel):
    request_id: str
    mode: Literal["mock", "dify"]
    context: NormalizedContext
    user_insight: UserInsightV01


class InsightEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    basis: Literal["explicit_brief", "contextual_inference", "behavioral_hypothesis"]
    confidence: Literal["low", "medium", "high"]
    validation_status: Literal["brief_supported", "needs_validation"]

    @model_validator(mode="after")
    def keep_evidence_and_status_consistent(self):
        if self.basis == "explicit_brief" and self.validation_status != "brief_supported":
            raise ValueError("explicit_brief evidence must be brief_supported")
        if self.basis != "explicit_brief" and self.validation_status != "needs_validation":
            raise ValueError("inferred evidence must need validation")
        if self.confidence == "high" and self.basis != "explicit_brief":
            raise ValueError("high confidence is only allowed for explicit brief evidence")
        return self


class JobToBeDone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job: str
    dimension: Literal["functional", "emotional", "social"]
    why_it_matters: str
    decision_relevance: Literal["primary", "secondary"]
    evidence: InsightEvidence


class InsightItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    insight: str
    why_it_matters: str
    decision_relevance: Literal["primary", "secondary"]
    evidence: InsightEvidence


class UserInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_user: TargetUser
    jobs_to_be_done: list[JobToBeDone] = Field(min_length=3, max_length=5)
    pain_points: list[InsightItem] = Field(min_length=2, max_length=5)
    purchase_motivations: list[InsightItem] = Field(min_length=2, max_length=5)
    adoption_barriers: list[InsightItem] = Field(min_length=2, max_length=5)
    typical_scenarios: list[InsightItem] = Field(min_length=2, max_length=5)
    research_questions: list[str] = Field(min_length=3, max_length=5)
    assumptions_to_validate: list[str] = Field(min_length=1, max_length=8)
    confidence: Literal["low", "medium", "high"]

    @model_validator(mode="after")
    def validate_v02_quality_contract(self):
        dimensions = {item.dimension for item in self.jobs_to_be_done}
        required = {"functional", "emotional", "social"}
        if not required.issubset(dimensions):
            raise ValueError(
                "jobs_to_be_done must include functional, emotional, and social dimensions"
            )

        sections = {
            "jobs_to_be_done": self.jobs_to_be_done,
            "pain_points": self.pain_points,
            "purchase_motivations": self.purchase_motivations,
            "adoption_barriers": self.adoption_barriers,
            "typical_scenarios": self.typical_scenarios,
        }
        missing_primary = [
            name
            for name, items in sections.items()
            if not any(item.decision_relevance == "primary" for item in items)
        ]
        if missing_primary:
            raise ValueError(
                "every insight section must include primary decision relevance: "
                + ", ".join(missing_primary)
            )
        return self


class QualityCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    label: str
    status: Literal["passed", "warning"]
    detail: str


class QualityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    path: str
    message: str


class QualityReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["passed", "passed_with_notes", "review_required"]
    issue_count: int = Field(ge=0)
    auto_revision_count: int = Field(ge=0)
    checks: list[QualityCheck] = Field(min_length=4, max_length=4)
    issues: list[QualityIssue]


class UserInsightResponse(BaseModel):
    request_id: str
    mode: Literal["mock", "dify"]
    context: NormalizedContext
    user_insight: UserInsight
    quality_review: QualityReview
