import asyncio

from app.models import BusinessGoal, GrowthBrief
from app.quality import evaluate_quality
from app.services import MockInsightService


BRIEF = GrowthBrief(
    product="AI Translation Earbuds",
    product_description="Real-time AI translation earbuds for cross-language communication.",
    target_market="United States",
    target_audience="Frequent international business travelers",
    business_goal=BusinessGoal.USER_ACQUISITION,
    additional_context="Entering the US market; test Reddit and TikTok.",
)


def mock_insight():
    return asyncio.run(MockInsightService().generate(BRIEF)).user_insight


def test_compliant_output_passes_quality_gate() -> None:
    review = evaluate_quality(mock_insight())

    assert review.status == "passed"
    assert review.issue_count == 0
    assert all(check.status == "passed" for check in review.checks)


def test_unsupported_causal_language_is_flagged() -> None:
    insight = mock_insight()
    first_motivation = insight.purchase_motivations[0].model_copy(
        update={"why_it_matters": "This improves conversion and increases revenue."}
    )
    insight = insight.model_copy(
        update={
            "purchase_motivations": [
                first_motivation,
                *insight.purchase_motivations[1:],
            ]
        }
    )

    review = evaluate_quality(insight)

    assert review.status == "review_required"
    assert any(issue.code == "unsupported_causality" for issue in review.issues)
    assert any(issue.path == "purchase_motivations.0.why_it_matters" for issue in review.issues)


def test_explicit_hypothesis_language_avoids_claim_warning() -> None:
    insight = mock_insight()
    first_motivation = insight.purchase_motivations[0].model_copy(
        update={"why_it_matters": "A hypothesis to test is that this may improve conversion."}
    )
    insight = insight.model_copy(
        update={
            "purchase_motivations": [
                first_motivation,
                *insight.purchase_motivations[1:],
            ]
        }
    )

    review = evaluate_quality(insight)

    assert not any(issue.code == "unsupported_causality" for issue in review.issues)


def test_research_question_order_is_flagged() -> None:
    insight = mock_insight().model_copy(
        update={"research_questions": ["Why would you buy this?", "What is hard?", "Would you switch?"]}
    )

    review = evaluate_quality(insight)

    assert review.status == "review_required"
    assert sum(issue.code == "research_question_pattern" for issue in review.issues) == 3
