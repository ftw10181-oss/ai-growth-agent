"""Deterministic evidence gate for AI Growth Agent V0.5.

The model may synthesize evidence, but it may not grade its own compliance.
This Code-node layer resolves source IDs, checks question provenance, rejects
weak retrieval matches, and enforces confidence ceilings before strategy nodes
consume the evidence brief.
"""

from __future__ import annotations

import copy
from typing import Any


MIN_RELEVANCE = 0.5


def _question_id(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get("question_id"), str):
        return value["question_id"]
    return None


def _has_snippet_only_limitation(source: dict[str, Any]) -> bool:
    return any(
        "snippet" in str(limitation).lower()
        for limitation in source.get("limitations", [])
    )


def _eligible_source_ids(
    source_ids: list[Any],
    finding_question_ids: set[str],
    sources: dict[str, dict[str, Any]],
    finding_path: str,
    issues: list[dict[str, str]],
) -> list[str]:
    eligible: list[str] = []
    for raw_source_id in source_ids:
        if not isinstance(raw_source_id, str) or raw_source_id not in sources:
            issues.append(
                {
                    "code": "unknown_source_id",
                    "path": finding_path,
                    "message": f"Removed unresolved source reference {raw_source_id!r}.",
                }
            )
            continue
        source = sources[raw_source_id]
        source_questions = {
            item for item in source.get("query_ids", []) if isinstance(item, str)
        }
        if not finding_question_ids.intersection(source_questions):
            issues.append(
                {
                    "code": "question_source_mismatch",
                    "path": finding_path,
                    "message": (
                        f"Removed {raw_source_id}; its query provenance does not "
                        "match the finding question."
                    ),
                }
            )
            continue
        try:
            relevance = float(source.get("relevance_score", 0))
        except (TypeError, ValueError):
            relevance = 0.0
        if relevance < MIN_RELEVANCE:
            issues.append(
                {
                    "code": "low_relevance_source",
                    "path": finding_path,
                    "message": (
                        f"Removed {raw_source_id}; relevance {relevance:.2f} is below "
                        f"the {MIN_RELEVANCE:.2f} evidence threshold."
                    ),
                }
            )
            continue
        if raw_source_id not in eligible:
            eligible.append(raw_source_id)
    return eligible


def _high_confidence_allowed(
    source_ids: list[str], sources: dict[str, dict[str, Any]]
) -> bool:
    supporting = [sources[source_id] for source_id in source_ids]
    if len(supporting) < 2:
        return False
    if not any(
        source.get("source_class") in {"primary", "independent_secondary"}
        for source in supporting
    ):
        return False
    if all(not source.get("published_at") for source in supporting):
        return False
    if all(_has_snippet_only_limitation(source) for source in supporting):
        return False
    return True


def main(
    evidence_brief: dict[str, Any],
    source_manifest: dict[str, Any],
    research_plan: dict[str, Any],
) -> dict[str, Any]:
    brief = copy.deepcopy(evidence_brief if isinstance(evidence_brief, dict) else {})
    manifest = source_manifest if isinstance(source_manifest, dict) else {}
    plan = research_plan if isinstance(research_plan, dict) else {}
    source_list = [
        source for source in manifest.get("sources", []) if isinstance(source, dict)
    ]
    sources = {
        source["source_id"]: source
        for source in source_list
        if isinstance(source.get("source_id"), str)
    }
    plan_question_ids = [
        question_id
        for question_id in (
            _question_id(question) for question in plan.get("questions", [])
        )
        if question_id
    ]
    issues: list[dict[str, str]] = []
    answered_question_ids: set[str] = set()

    for index, finding in enumerate(brief.get("findings", [])):
        if not isinstance(finding, dict):
            continue
        path = f"findings.{index}"
        finding_question_ids = {
            item
            for item in finding.get("research_question_ids", [])
            if isinstance(item, str)
        }
        supporting = _eligible_source_ids(
            finding.get("supporting_source_ids", []),
            finding_question_ids,
            sources,
            f"{path}.supporting_source_ids",
            issues,
        )
        contradicting = _eligible_source_ids(
            finding.get("contradicting_source_ids", []),
            finding_question_ids,
            sources,
            f"{path}.contradicting_source_ids",
            issues,
        )
        finding["supporting_source_ids"] = supporting
        finding["contradicting_source_ids"] = contradicting

        if not supporting:
            if finding.get("status") != "insufficient":
                issues.append(
                    {
                        "code": "finding_downgraded",
                        "path": f"{path}.status",
                        "message": "Downgraded to insufficient after evidence checks.",
                    }
                )
            finding["status"] = "insufficient"
            finding["confidence"] = "low"
            finding["contradicting_source_ids"] = []
            limitations = finding.setdefault("limitations", [])
            note = "No eligible source passed provenance and relevance checks."
            if note not in limitations:
                if len(limitations) < 5:
                    limitations.append(note)
                else:
                    limitations[-1] = note
            continue

        if finding.get("status") == "contested" and not contradicting:
            finding["status"] = "supported"
            issues.append(
                {
                    "code": "conflict_downgraded",
                    "path": f"{path}.status",
                    "message": "Removed contested status because no eligible contradiction remained.",
                }
            )

        if finding.get("confidence") == "high" and not _high_confidence_allowed(
            supporting, sources
        ):
            finding["confidence"] = "medium"
            issues.append(
                {
                    "code": "confidence_capped",
                    "path": f"{path}.confidence",
                    "message": (
                        "Capped confidence at medium because high-confidence "
                        "source requirements were not met."
                    ),
                }
            )

        if finding.get("status") in {"supported", "contested"}:
            answered_question_ids.update(finding_question_ids)

    coverage = brief.setdefault("source_coverage", {})
    coverage["retained_source_count"] = len(source_list)
    coverage["question_count"] = len(plan_question_ids)
    coverage["answered_question_count"] = len(
        answered_question_ids.intersection(plan_question_ids)
    )

    issues = issues[:50]
    return {
        "validated_evidence_brief": brief,
        "evidence_audit": {
            "status": "passed_with_notes" if issues else "passed",
            "issue_count": len(issues),
            "issues": issues,
            "minimum_relevance": MIN_RELEVANCE,
        },
    }
