from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


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


class JobToBeDone(BaseModel):
    job: str
    dimension: str
    why_it_matters: str


class InsightItem(BaseModel):
    insight: str
    why_it_matters: str


class UserInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    target_user: TargetUser
    jobs_to_be_done: list[JobToBeDone] = Field(min_length=3, max_length=5)
    pain_points: list[InsightItem] = Field(min_length=3, max_length=5)
    purchase_motivations: list[InsightItem] = Field(min_length=3, max_length=5)
    adoption_barriers: list[InsightItem] = Field(min_length=3, max_length=5)
    typical_scenarios: list[InsightItem] = Field(min_length=3, max_length=5)
    research_questions: list[str] = Field(min_length=3, max_length=5)
    assumptions_to_validate: list[str] = Field(min_length=1, max_length=8)
    confidence: str = Field(pattern="^(low|medium|high)$")


class UserInsightResponse(BaseModel):
    request_id: str
    mode: str
    context: NormalizedContext
    user_insight: UserInsight

