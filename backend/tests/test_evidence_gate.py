import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).parents[2] / "dify" / "code" / "validate_evidence_brief.py"
)
SPEC = importlib.util.spec_from_file_location("validate_evidence_brief", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def _source(
    source_id: str,
    query_id: str,
    relevance: float,
    *,
    published_at=None,
    source_class="independent_secondary",
    limitations=None,
):
    return {
        "source_id": source_id,
        "query_ids": [query_id],
        "relevance_score": relevance,
        "published_at": published_at,
        "source_class": source_class,
        "limitations": limitations or ["Evaluation used a snippet."],
    }


def _brief(source_ids, confidence="high"):
    return {
        "summary": "A sufficiently descriptive evidence summary for the decision.",
        "findings": [
            {
                "finding_id": "EV-001",
                "research_question_ids": ["RQ-001"],
                "claim": "A sufficiently descriptive evidence finding for testing.",
                "dimension": "user_behavior",
                "status": "supported",
                "supporting_source_ids": source_ids,
                "contradicting_source_ids": [],
                "confidence": confidence,
                "implication": "Use this evidence to prioritize the next validation step.",
                "limitations": [],
            }
        ],
        "research_gaps": [
            {
                "gap": "More direct user evidence is needed.",
                "decision_risk": "The selected direction may be wrong.",
                "next_step": "Conduct target-user interviews.",
                "priority": "important",
            }
        ],
        "source_coverage": {
            "retained_source_count": 0,
            "question_count": 0,
            "answered_question_count": 0,
            "source_diversity_note": "Coverage is recalculated by the gate.",
        },
    }


def test_gate_caps_high_confidence_for_unknown_date_and_snippet_only_sources():
    result = MODULE.main(
        evidence_brief=_brief(["SRC-001", "SRC-002"]),
        source_manifest={
            "sources": [
                _source("SRC-001", "RQ-001", 0.8),
                _source("SRC-002", "RQ-001", 0.7),
            ]
        },
        research_plan={"questions": [{"question_id": "RQ-001"}]},
    )

    finding = result["validated_evidence_brief"]["findings"][0]
    assert finding["status"] == "supported"
    assert finding["confidence"] == "medium"
    assert result["evidence_audit"]["status"] == "passed_with_notes"


def test_gate_rejects_question_mismatch_and_low_relevance_sources():
    result = MODULE.main(
        evidence_brief=_brief(["SRC-001", "SRC-002"]),
        source_manifest={
            "sources": [
                _source("SRC-001", "RQ-002", 0.9, published_at="2026-08-01"),
                _source("SRC-002", "RQ-001", 0.39, published_at="2026-08-01"),
            ]
        },
        research_plan={
            "questions": [
                {"question_id": "RQ-001"},
                {"question_id": "RQ-002"},
            ]
        },
    )

    brief = result["validated_evidence_brief"]
    finding = brief["findings"][0]
    assert finding["status"] == "insufficient"
    assert finding["confidence"] == "low"
    assert finding["supporting_source_ids"] == []
    assert brief["source_coverage"]["answered_question_count"] == 0
    assert {issue["code"] for issue in result["evidence_audit"]["issues"]} >= {
        "question_source_mismatch",
        "low_relevance_source",
        "finding_downgraded",
    }


def test_gate_preserves_compliant_high_confidence_finding():
    result = MODULE.main(
        evidence_brief=_brief(["SRC-001", "SRC-002"]),
        source_manifest={
            "sources": [
                _source(
                    "SRC-001",
                    "RQ-001",
                    0.8,
                    published_at="2026-08-01",
                    limitations=["Full report reviewed."],
                ),
                _source(
                    "SRC-002",
                    "RQ-001",
                    0.7,
                    published_at="2026-07-01",
                    source_class="primary",
                    limitations=["Methodology is disclosed."],
                ),
            ]
        },
        research_plan={"questions": [{"question_id": "RQ-001"}]},
    )

    finding = result["validated_evidence_brief"]["findings"][0]
    assert finding["confidence"] == "high"
    assert result["evidence_audit"]["status"] == "passed"
