import pytest
from pydantic import ValidationError

from app.models import (
    ClaimCitation,
    EvidenceFinding,
    ResearchPlan,
    SourceManifest,
)


def _question(question_id: str, priority: str = "important") -> dict:
    return {
        "question_id": question_id,
        "question": "Which current behavior signal could change the initial growth wedge?",
        "dimension": "user_behavior",
        "decision_impact": "Determines which entry scenario should be tested first.",
        "evidence_needed": "Recent observable behavior from the target market.",
        "query": "United States professional social discovery behavior 2026",
        "recency_preference": "last_12_months",
        "priority": priority,
    }


def test_research_plan_requires_unique_ids_and_critical_question():
    plan = ResearchPlan.model_validate({
        "decision_context": "Choose the initial growth wedge before scaling acquisition.",
        "questions": [
            _question("RQ-001", "critical"),
            _question("RQ-002"),
            _question("RQ-003", "exploratory"),
        ],
        "search_limits": {
            "max_queries": 5,
            "max_results_per_query": 5,
            "max_retained_sources": 10,
        },
    })

    assert len(plan.questions) == 3

    with pytest.raises(ValidationError):
        ResearchPlan.model_validate({
            **plan.model_dump(mode="json"),
            "questions": [_question("RQ-001", "critical"), _question("RQ-001"), _question("RQ-003")],
        })


def test_contested_finding_preserves_both_sides_and_cannot_be_high_confidence():
    valid = {
        "finding_id": "EV-001",
        "research_question_ids": ["RQ-001"],
        "claim": "The retained sources disagree on whether offline events are the preferred discovery path.",
        "dimension": "user_behavior",
        "status": "contested",
        "supporting_source_ids": ["SRC-001"],
        "contradicting_source_ids": ["SRC-002"],
        "confidence": "medium",
        "implication": "Keep the entry scenario open until primary research resolves the conflict.",
        "limitations": ["Both sources use different audience definitions."],
    }
    assert EvidenceFinding.model_validate(valid).status == "contested"

    with pytest.raises(ValidationError):
        EvidenceFinding.model_validate({**valid, "confidence": "high"})


def test_evidence_backed_citation_requires_a_finding():
    with pytest.raises(ValidationError):
        ClaimCitation.model_validate({
            "claim_path": "market_hypothesis.growth_wedge.entry_scenario",
            "finding_ids": [],
            "claim_status": "evidence_backed",
            "explanation": "The claim needs direct evidence.",
        })


def test_source_manifest_rejects_duplicate_urls():
    source = {
        "source_id": "SRC-001",
        "title": "Example research source",
        "url": "https://example.com/report",
        "domain": "example.com",
        "publisher": "Example",
        "published_at": "2026-07-01",
        "retrieved_at": "2026-08-22T00:00:00Z",
        "query_ids": ["RQ-001"],
        "source_class": "independent_secondary",
        "relevance_score": 0.8,
        "freshness": "current",
        "snippet": "A sufficiently long excerpt returned by the search tool.",
        "limitations": ["Methodology details require review."],
    }

    with pytest.raises(ValidationError):
        SourceManifest.model_validate({
            "research_status": "complete",
            "researched_at": "2026-08-22T00:00:00Z",
            "sources": [source, {**source, "source_id": "SRC-002"}],
            "failed_query_ids": [],
        })

