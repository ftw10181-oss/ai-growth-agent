import pytest
from pydantic import ValidationError

from app.models import BusinessGoal, GrowthBrief, InsightEvidence
from app.services import MockInsightService


BRIEF = GrowthBrief(
    product="AI Translation Earbuds",
    product_description="Real-time AI translation earbuds for cross-language communication.",
    target_market="United States",
    target_audience="Frequent international business travelers",
    business_goal=BusinessGoal.USER_ACQUISITION,
    additional_context="Entering the US market; test Reddit and TikTok.",
)


def test_v02_mock_attaches_evidence_to_every_insight() -> None:
    import asyncio

    response = asyncio.run(MockInsightService().generate(BRIEF))
    insight = response.user_insight
    sections = (
        insight.jobs_to_be_done,
        insight.pain_points,
        insight.purchase_motivations,
        insight.adoption_barriers,
        insight.typical_scenarios,
    )

    assert all(item.evidence.validation_status for section in sections for item in section)
    assert all(item.decision_relevance for section in sections for item in section)
    assert all(
        any(item.decision_relevance == "primary" for item in section) for section in sections
    )


def test_every_major_section_requires_primary_relevance() -> None:
    import asyncio

    response = asyncio.run(MockInsightService().generate(BRIEF))
    payload = response.user_insight.model_dump()
    payload["adoption_barriers"] = [
        {**item, "decision_relevance": "secondary"} for item in payload["adoption_barriers"]
    ]

    with pytest.raises(
        ValidationError,
        match="every insight section must include primary decision relevance",
    ):
        response.user_insight.__class__.model_validate(payload)


def test_inferred_evidence_cannot_claim_brief_support() -> None:
    with pytest.raises(ValidationError, match="inferred evidence must need validation"):
        InsightEvidence(
            basis="behavioral_hypothesis",
            confidence="low",
            validation_status="brief_supported",
        )


def test_high_confidence_requires_explicit_brief_evidence() -> None:
    with pytest.raises(ValidationError, match="high confidence"):
        InsightEvidence(
            basis="contextual_inference",
            confidence="high",
            validation_status="needs_validation",
        )
