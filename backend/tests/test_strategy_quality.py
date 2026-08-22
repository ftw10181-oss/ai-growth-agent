import asyncio

from app.models import BusinessGoal, GrowthBrief, InsightEvidence
from app.services import MockInsightService
from app.strategy_quality import evaluate_strategy_quality, normalize_strategy_claim_language


BRIEF = GrowthBrief(
    product="AI Translation Earbuds",
    product_description="Real-time AI translation earbuds for cross-language communication.",
    target_market="United States",
    target_audience="Frequent international business travelers",
    business_goal=BusinessGoal.USER_ACQUISITION,
    additional_context="Entering the US market; test Reddit and TikTok.",
)


def mock_strategy():
    return asyncio.run(MockInsightService().generate_strategy(BRIEF))


def review(strategy):
    return evaluate_strategy_quality(
        BRIEF,
        strategy.context,
        strategy.user_insight,
        strategy.market_hypothesis,
        strategy.value_proposition,
    )


def test_compliant_strategy_passes_cross_module_gate() -> None:
    result = mock_strategy()

    assert result.quality_review.status == "passed"
    assert result.quality_review.issue_count == 0
    assert all(check.status == "passed" for check in result.quality_review.checks)


def test_invalid_source_reference_blocks_strategy() -> None:
    strategy = mock_strategy()
    opportunity = strategy.market_hypothesis.opportunity_statement.model_copy(
        update={"source_refs": ["context.missing_field"]}
    )
    market = strategy.market_hypothesis.model_copy(
        update={"opportunity_statement": opportunity}
    )
    strategy = strategy.model_copy(update={"market_hypothesis": market})

    result = review(strategy)

    assert result.status == "review_required"
    assert any(issue.code == "invalid_source_ref" for issue in result.issues)


def test_downstream_evidence_cannot_exceed_weakest_source() -> None:
    strategy = mock_strategy()
    primary = strategy.value_proposition.primary_value.model_copy(
        update={
            "source_refs": ["user_insight.jobs_to_be_done.1.job"],
            "evidence": InsightEvidence(
                basis="explicit_brief",
                confidence="high",
                validation_status="brief_supported",
            ),
        }
    )
    value = strategy.value_proposition.model_copy(update={"primary_value": primary})
    strategy = strategy.model_copy(update={"value_proposition": value})

    result = review(strategy)

    assert any(issue.code == "evidence_stronger_than_source" for issue in result.issues)
    assert result.blocking_issue_count >= 1


def test_explicit_competitor_claim_requires_review() -> None:
    strategy = mock_strategy()
    alternative = strategy.market_hypothesis.current_alternatives[0].model_copy(
        update={
            "limitation_hypothesis": "Existing tools often fail to provide real-time communication.",
            "evidence": InsightEvidence(
                basis="explicit_brief",
                confidence="high",
                validation_status="brief_supported",
            ),
        }
    )
    market = strategy.market_hypothesis.model_copy(
        update={
            "current_alternatives": [
                alternative,
                *strategy.market_hypothesis.current_alternatives[1:],
            ]
        }
    )
    strategy = strategy.model_copy(update={"market_hypothesis": market})

    result = review(strategy)

    assert result.status == "review_required"
    assert any(issue.code == "unsupported_explicit_market_claim" for issue in result.issues)


def test_primary_value_must_link_user_and_market_decisions() -> None:
    strategy = mock_strategy()
    primary = strategy.value_proposition.primary_value.model_copy(
        update={"source_refs": ["user_insight.jobs_to_be_done.0.job"]}
    )
    value = strategy.value_proposition.model_copy(update={"primary_value": primary})
    strategy = strategy.model_copy(update={"value_proposition": value})

    result = review(strategy)

    assert any(issue.code == "primary_value_missing_decision_link" for issue in result.issues)


def test_vague_validation_signals_are_non_blocking_notes() -> None:
    strategy = mock_strategy()
    priority = strategy.market_hypothesis.validation_priorities[0].model_copy(
        update={"pass_signal": "High user interest after interviews.", "fail_signal": "Low user interest after interviews."}
    )
    market = strategy.market_hypothesis.model_copy(
        update={
            "validation_priorities": [
                priority,
                *strategy.market_hypothesis.validation_priorities[1:],
            ]
        }
    )
    strategy = strategy.model_copy(update={"market_hypothesis": market})

    result = review(strategy)

    assert result.status == "passed_with_notes"
    assert result.blocking_issue_count == 0
    assert any(issue.code == "validation_signal_not_measurable" for issue in result.issues)


def test_inferred_comparison_is_reframed_before_strategy_review() -> None:
    strategy = mock_strategy()
    frame = strategy.market_hypothesis.competitive_frame.model_copy(
        update={
            "differentiation_hypothesis": (
                "The earbuds provide real-time translations without connectivity issues, "
                "unlike smartphone apps."
            )
        }
    )
    market = strategy.market_hypothesis.model_copy(update={"competitive_frame": frame})

    normalized_market, normalized_value, revision_count = normalize_strategy_claim_language(
        market, strategy.value_proposition
    )
    result = evaluate_strategy_quality(
        BRIEF,
        strategy.context,
        strategy.user_insight,
        normalized_market,
        normalized_value,
        revision_count,
    )

    assert normalized_market.competitive_frame.differentiation_hypothesis.startswith(
        "Hypothesis to test —"
    )
    assert result.status == "passed"
    assert result.auto_revision_count == 1
    assert not any(issue.code == "unsupported_claim_language" for issue in result.issues)
