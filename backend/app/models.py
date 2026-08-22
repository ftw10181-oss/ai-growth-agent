from datetime import date, datetime
from enum import Enum
from typing import Annotated, Literal, Optional

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


SourceRef = Annotated[
    str,
    Field(pattern=r"^(context|user_insight|market_hypothesis)\."),
]
Priority = Literal["critical", "important", "exploratory"]


class OpportunityStatement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis: str = Field(min_length=20)
    why_now: str = Field(min_length=15)
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class CurrentAlternative(BaseModel):
    model_config = ConfigDict(extra="forbid")

    alternative: str = Field(min_length=4)
    limitation_hypothesis: str = Field(min_length=12)
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class BehaviorHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis: str = Field(min_length=15)
    trigger: str = Field(min_length=8)
    expected_observation: str = Field(min_length=12)
    priority: Priority
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class GrowthWedge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    segment: str = Field(min_length=8)
    entry_scenario: str = Field(min_length=12)
    rationale: str = Field(min_length=15)
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class CompetitiveFrame(BaseModel):
    model_config = ConfigDict(extra="forbid")

    compared_with: list[str] = Field(min_length=1, max_length=5)
    differentiation_hypothesis: str = Field(min_length=15)
    less_suitable_for: str = Field(min_length=10)
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class MarketRisk(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk: str = Field(min_length=10)
    consequence: str = Field(min_length=10)
    priority: Priority
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class ValidationPriority(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hypothesis_to_test: str = Field(min_length=15)
    method: str = Field(min_length=8)
    pass_signal: str = Field(min_length=10)
    fail_signal: str = Field(min_length=10)
    priority: Priority
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)


class MarketHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    opportunity_statement: OpportunityStatement
    current_alternatives: list[CurrentAlternative] = Field(min_length=2, max_length=5)
    behavior_hypotheses: list[BehaviorHypothesis] = Field(min_length=3, max_length=5)
    growth_wedge: GrowthWedge
    competitive_frame: CompetitiveFrame
    main_risks: list[MarketRisk] = Field(min_length=3, max_length=5)
    validation_priorities: list[ValidationPriority] = Field(min_length=3, max_length=5)
    confidence: Literal["low", "medium", "high"]

    @model_validator(mode="after")
    def require_critical_priorities(self):
        sections = {
            "behavior_hypotheses": self.behavior_hypotheses,
            "main_risks": self.main_risks,
            "validation_priorities": self.validation_priorities,
        }
        missing = [
            name
            for name, items in sections.items()
            if not any(item.priority == "critical" for item in items)
        ]
        if missing:
            raise ValueError("market sections require a critical priority: " + ", ".join(missing))
        return self


class PrimaryValue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str = Field(min_length=12)
    value_type: Literal["functional", "emotional", "social"]
    rationale: str = Field(min_length=12)
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class ValueItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement: str = Field(min_length=10)
    why_it_matters: str = Field(min_length=10)
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class ReasonToBelieve(BaseModel):
    model_config = ConfigDict(extra="forbid")

    capability: str = Field(min_length=6)
    support_status: Literal["brief_supported", "needs_confirmation"]
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)


class MessagePillar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=3)
    message: str = Field(min_length=12)
    user_problem: str = Field(min_length=10)
    priority: Literal["primary", "secondary"]
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class Objection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objection: str = Field(min_length=8)
    response_hypothesis: str = Field(min_length=12)
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)
    evidence: InsightEvidence


class MessageTest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    angle: Literal[
        "feature_led", "pain_led", "scenario_led", "confidence_led", "social_value_led"
    ]
    variant_a: str = Field(min_length=10)
    variant_b: str = Field(min_length=10)
    primary_metric: str = Field(min_length=3)
    expected_learning: str = Field(min_length=12)
    source_refs: list[SourceRef] = Field(min_length=1, max_length=5)


class ValueProposition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_value: PrimaryValue
    functional_values: list[ValueItem] = Field(min_length=1, max_length=3)
    emotional_values: list[ValueItem] = Field(min_length=1, max_length=3)
    social_values: list[ValueItem] = Field(min_length=1, max_length=3)
    positioning_statement: str = Field(min_length=40)
    reasons_to_believe: list[ReasonToBelieve] = Field(min_length=1, max_length=4)
    message_pillars: list[MessagePillar] = Field(min_length=3, max_length=4)
    objections: list[Objection] = Field(min_length=3, max_length=5)
    message_tests: list[MessageTest] = Field(min_length=3, max_length=4)
    confidence: Literal["low", "medium", "high"]

    @model_validator(mode="after")
    def require_primary_message_pillar(self):
        if not any(item.priority == "primary" for item in self.message_pillars):
            raise ValueError("message_pillars must include a primary priority")
        return self


class StrategySummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_user: str
    growth_wedge: str
    primary_value: str
    biggest_risk: str


class StrategyQualityIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    path: str
    message: str
    severity: Literal["low", "medium", "high"]
    blocking: bool


class StrategyQualityReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["passed", "passed_with_notes", "review_required"]
    issue_count: int = Field(ge=0)
    blocking_issue_count: int = Field(ge=0)
    auto_revision_count: int = Field(ge=0)
    checks: list[QualityCheck] = Field(min_length=6, max_length=7)
    issues: list[StrategyQualityIssue]


class StrategyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    mode: Literal["mock", "dify"]
    strategy_summary: StrategySummary
    context: NormalizedContext
    user_insight: UserInsight
    market_hypothesis: MarketHypothesis
    value_proposition: ValueProposition
    quality_review: StrategyQualityReview


ResearchDimension = Literal[
    "user_behavior",
    "market_context",
    "competitor",
    "channel",
    "risk",
    "product_expectation",
]


class ResearchQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(pattern=r"^RQ-[0-9]{3}$")
    question: str = Field(min_length=15, max_length=240)
    dimension: ResearchDimension
    decision_impact: str = Field(min_length=15, max_length=300)
    evidence_needed: str = Field(min_length=15, max_length=300)
    query: str = Field(min_length=8, max_length=220)
    recency_preference: Literal["last_12_months", "last_24_months", "any"]
    priority: Priority


class SearchLimits(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_queries: Literal[5]
    max_results_per_query: int = Field(ge=3, le=5)
    max_retained_sources: Literal[10]


class ResearchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_context: str = Field(min_length=20, max_length=500)
    questions: list[ResearchQuestion] = Field(min_length=3, max_length=5)
    search_limits: SearchLimits

    @model_validator(mode="after")
    def require_unique_questions_and_critical_priority(self):
        ids = [question.question_id for question in self.questions]
        if len(ids) != len(set(ids)):
            raise ValueError("research question IDs must be unique")
        if not any(question.priority == "critical" for question in self.questions):
            raise ValueError("research plan must include a critical question")
        return self


class ResearchSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(pattern=r"^SRC-[0-9]{3}$")
    title: str = Field(min_length=3, max_length=300)
    url: str = Field(pattern=r"^https://")
    domain: str = Field(min_length=3, max_length=253)
    publisher: Optional[str] = Field(default=None, max_length=160)
    published_at: Optional[date] = None
    retrieved_at: datetime
    query_ids: list[str] = Field(min_length=1, max_length=5)
    source_class: Literal[
        "primary", "independent_secondary", "vendor", "community", "unknown"
    ]
    relevance_score: float = Field(ge=0, le=1)
    freshness: Literal["current", "dated", "unknown"]
    snippet: str = Field(min_length=10, max_length=1200)
    limitations: list[str] = Field(max_length=4)

    @model_validator(mode="after")
    def validate_query_ids(self):
        if len(self.query_ids) != len(set(self.query_ids)):
            raise ValueError("source query IDs must be unique")
        if not all(
            len(value) == 6 and value.startswith("RQ-") and value[3:].isdigit()
            for value in self.query_ids
        ):
            raise ValueError("source query IDs must use the RQ-000 pattern")
        return self


class SourceManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    research_status: Literal["complete", "partial", "unavailable", "offline_fixture"]
    researched_at: datetime
    sources: list[ResearchSource] = Field(max_length=10)
    failed_query_ids: list[str] = Field(max_length=5)

    @model_validator(mode="after")
    def validate_source_manifest(self):
        ids = [source.source_id for source in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("source IDs must be unique")
        urls = [source.url for source in self.sources]
        if len(urls) != len(set(urls)):
            raise ValueError("source URLs must be canonical and unique")
        if self.research_status == "unavailable" and self.sources:
            raise ValueError("unavailable research cannot contain sources")
        return self


class EvidenceFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    finding_id: str = Field(pattern=r"^EV-[0-9]{3}$")
    research_question_ids: list[str] = Field(min_length=1, max_length=5)
    claim: str = Field(min_length=15, max_length=500)
    dimension: ResearchDimension
    status: Literal["supported", "contested", "insufficient"]
    supporting_source_ids: list[str] = Field(max_length=6)
    contradicting_source_ids: list[str] = Field(max_length=6)
    confidence: Literal["low", "medium", "high"]
    implication: str = Field(min_length=12, max_length=500)
    limitations: list[str] = Field(max_length=5)

    @model_validator(mode="after")
    def keep_status_and_confidence_consistent(self):
        if self.status == "contested":
            if not self.supporting_source_ids or not self.contradicting_source_ids:
                raise ValueError("contested findings need supporting and contradicting sources")
            if self.confidence == "high":
                raise ValueError("contested findings cannot have high confidence")
        if self.status == "supported" and not self.supporting_source_ids:
            raise ValueError("supported findings need at least one supporting source")
        if self.status == "insufficient" and self.confidence != "low":
            raise ValueError("insufficient findings must have low confidence")
        return self


class ResearchGap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gap: str = Field(min_length=8, max_length=300)
    decision_risk: str = Field(min_length=8, max_length=300)
    next_step: str = Field(min_length=8, max_length=300)
    priority: Priority


class SourceCoverage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    retained_source_count: int = Field(ge=0, le=10)
    question_count: int = Field(ge=3, le=5)
    answered_question_count: int = Field(ge=0, le=5)
    source_diversity_note: str = Field(min_length=8, max_length=400)


class EvidenceBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=30, max_length=800)
    findings: list[EvidenceFinding] = Field(min_length=3, max_length=10)
    research_gaps: list[ResearchGap] = Field(min_length=1, max_length=8)
    source_coverage: SourceCoverage

    @model_validator(mode="after")
    def require_unique_finding_ids(self):
        ids = [finding.finding_id for finding in self.findings]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence finding IDs must be unique")
        return self


class EvidenceAuditIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=3, max_length=80)
    path: str = Field(min_length=3, max_length=200)
    message: str = Field(min_length=8, max_length=500)


class EvidenceAudit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["passed", "passed_with_notes"]
    issue_count: int = Field(ge=0)
    issues: list[EvidenceAuditIssue] = Field(max_length=50)
    minimum_relevance: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def issue_count_matches_items(self):
        if self.issue_count != len(self.issues):
            raise ValueError("evidence audit issue_count must match issues")
        if self.status == "passed" and self.issues:
            raise ValueError("a passed evidence audit cannot contain issues")
        return self


class ClaimCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_path: str = Field(
        pattern=r"^(user_insight|market_hypothesis|value_proposition)\."
    )
    finding_ids: list[str] = Field(max_length=5)
    claim_status: Literal["evidence_backed", "contested", "inference", "unknown"]
    explanation: str = Field(min_length=8, max_length=400)

    @model_validator(mode="after")
    def require_findings_for_evidence_claims(self):
        if self.claim_status in {"evidence_backed", "contested"} and not self.finding_ids:
            raise ValueError("evidence-backed and contested claims require finding IDs")
        return self


class ClaimCitationMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    citations: list[ClaimCitation] = Field(min_length=1, max_length=30)

    @model_validator(mode="after")
    def require_unique_claim_paths(self):
        paths = [citation.claim_path for citation in self.citations]
        if len(paths) != len(set(paths)):
            raise ValueError("claim citation paths must be unique")
        return self


class ResearchDecisionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_coverage: str
    largest_research_gap: str


class ResearchQualityReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["passed", "passed_with_notes", "review_required"]
    issue_count: int = Field(ge=0)
    blocking_issue_count: int = Field(ge=0)
    auto_revision_count: int = Field(ge=0)
    checks: list[QualityCheck] = Field(min_length=8, max_length=8)
    issues: list[StrategyQualityIssue]


class ResearchStrategyResponse(StrategyResponse):
    model_config = ConfigDict(extra="forbid")

    research_status: Literal["complete", "partial", "unavailable", "offline_fixture"]
    researched_at: datetime
    research_plan: ResearchPlan
    source_manifest: SourceManifest
    evidence_brief: EvidenceBrief
    evidence_audit: EvidenceAudit
    claim_citations: ClaimCitationMap
    research_summary: ResearchDecisionSummary
    research_quality_review: ResearchQualityReview
