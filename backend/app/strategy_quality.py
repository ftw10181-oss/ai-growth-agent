from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Any

from .models import (
    GrowthBrief,
    InsightEvidence,
    MarketHypothesis,
    NormalizedContext,
    QualityCheck,
    StrategyQualityIssue,
    StrategyQualityReview,
    UserInsight,
    ValueProposition,
)


MARKET_ASSERTION_PATTERN = re.compile(
    r"\b(?:unlike|market demand|users? prefer|customers? prefer|willingness to pay|"
    r"willing to pay|existing (?:\w+\s+){0,2}(?:tools|apps|products)|"
    r"(?:tools|apps|competitors?)\b.{0,40}\b(?:fail|fails|lack|lacks|cannot|can't|"
    r"may not|do not|does not|are not|cause|causes))\b",
    re.IGNORECASE,
)
UNSUPPORTED_STRENGTH_PATTERN = re.compile(
    r"\b(?:many|most|often|frequently|significantly|better than|worse than)\b",
    re.IGNORECASE,
)
HYPOTHESIS_MARKER = re.compile(r"\b(?:may|might|could|hypothesis|to test)\b", re.IGNORECASE)
MEASURABLE_SIGNAL = re.compile(
    r"(?:\d|%|percent|at least|at most|no more than|fewer than|more than|within \d)",
    re.IGNORECASE,
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)

BASIS_RANK = {
    "behavioral_hypothesis": 1,
    "contextual_inference": 2,
    "explicit_brief": 3,
}
CONFIDENCE_RANK = {"low": 1, "medium": 2, "high": 3}


def _issue(
    code: str,
    path: str,
    message: str,
    *,
    severity: str = "medium",
    blocking: bool = False,
) -> StrategyQualityIssue:
    return StrategyQualityIssue(
        code=code,
        path=path,
        message=message,
        severity=severity,
        blocking=blocking,
    )


def _traceable_items(value: Any, path: str) -> Iterator[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        if isinstance(value.get("source_refs"), list):
            yield path, value
        for key, child in value.items():
            yield from _traceable_items(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _traceable_items(child, f"{path}.{index}")


def _evidenced_user_items(
    value: Any, path: str = "user_insight"
) -> Iterator[tuple[str, dict[str, Any]]]:
    if isinstance(value, dict):
        if isinstance(value.get("evidence"), dict):
            yield path, value
        for key, child in value.items():
            yield from _evidenced_user_items(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _evidenced_user_items(child, f"{path}.{index}")


def _resolve_ref(reference: str, roots: dict[str, Any]) -> tuple[bool, Any, InsightEvidence | None]:
    parts = reference.split(".")
    current = roots.get(parts[0])
    if current is None:
        return False, None, None

    inherited_evidence: InsightEvidence | None = None
    for part in parts[1:]:
        if isinstance(current, dict) and isinstance(current.get("evidence"), dict):
            inherited_evidence = InsightEvidence.model_validate(current["evidence"])
        if isinstance(current, dict) and part in current:
            current = current[part]
        elif isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
        else:
            return False, None, None

    if isinstance(current, dict) and isinstance(current.get("evidence"), dict):
        inherited_evidence = InsightEvidence.model_validate(current["evidence"])
    if parts[0] == "context" and inherited_evidence is None:
        inferred_fields = {"product_category", "assumptions", "ambiguities"}
        basis = (
            "contextual_inference"
            if len(parts) > 1 and parts[1] in inferred_fields
            else "explicit_brief"
        )
        inherited_evidence = InsightEvidence(
            basis=basis,
            confidence="medium" if basis == "contextual_inference" else "high",
            validation_status="needs_validation"
            if basis == "contextual_inference"
            else "brief_supported",
        )
    return True, current, inherited_evidence


def _item_text(item: dict[str, Any]) -> str:
    ignored = {"source_refs", "evidence", "priority", "support_status"}
    return " ".join(
        str(value) for key, value in item.items() if key not in ignored and isinstance(value, str)
    )


def _tokens(text: str) -> set[str]:
    stop = {"the", "a", "an", "and", "or", "to", "for", "of", "in", "on", "with", "is", "are"}
    return {token.lower() for token in TOKEN_PATTERN.findall(text) if token.lower() not in stop}


def normalize_strategy_claim_language(
    market_hypothesis: MarketHypothesis,
    value_proposition: ValueProposition,
) -> tuple[MarketHypothesis, ValueProposition, int]:
    """Make inferred market assertions visibly testable before quality review.

    The rewrite is intentionally conservative: it never upgrades evidence or
    changes the substance of a generated claim. Explicit-brief claims are left
    untouched so a wrongly attributed factual claim still blocks publication.
    """
    market_data = market_hypothesis.model_dump(mode="json")
    value_data = value_proposition.model_dump(mode="json")
    revision_count = 0

    for root_name, payload in (
        ("market_hypothesis", market_data),
        ("value_proposition", value_data),
    ):
        for _, item in _traceable_items(payload, root_name):
            raw_evidence = item.get("evidence")
            if not isinstance(raw_evidence, dict):
                continue
            evidence = InsightEvidence.model_validate(raw_evidence)
            if evidence.basis == "explicit_brief":
                continue
            for key, value in item.items():
                if key in {"source_refs", "evidence", "priority", "support_status"}:
                    continue
                if not isinstance(value, str) or HYPOTHESIS_MARKER.search(value):
                    continue
                if MARKET_ASSERTION_PATTERN.search(value) or UNSUPPORTED_STRENGTH_PATTERN.search(
                    value
                ):
                    item[key] = f"Hypothesis to test — {value}"
                    revision_count += 1

    return (
        MarketHypothesis.model_validate(market_data),
        ValueProposition.model_validate(value_data),
        revision_count,
    )


def evaluate_strategy_quality(
    brief: GrowthBrief,
    context: NormalizedContext,
    user_insight: UserInsight,
    market_hypothesis: MarketHypothesis,
    value_proposition: ValueProposition,
    auto_revision_count: int = 0,
) -> StrategyQualityReview:
    """Validate reference integrity, evidence inheritance, and decision continuity."""
    issues: list[StrategyQualityIssue] = []
    context_data = context.model_dump(mode="json")
    user_data = user_insight.model_dump(mode="json")
    market_data = market_hypothesis.model_dump(mode="json")
    value_data = value_proposition.model_dump(mode="json")
    roots = {
        "context": context_data,
        "user_insight": user_data,
        "market_hypothesis": market_data,
    }

    traceable = [
        *_traceable_items(market_data, "market_hypothesis"),
        *_traceable_items(value_data, "value_proposition"),
    ]
    reference_issues = 0
    evidence_issues = 0
    claim_issues = 0
    grounding_issues = 0

    for path, item in traceable:
        allowed_roots = (
            {"context", "user_insight"}
            if path.startswith("market_hypothesis")
            else {"context", "user_insight", "market_hypothesis"}
        )
        source_evidence: list[InsightEvidence] = []
        for reference in item["source_refs"]:
            if reference.split(".", 1)[0] not in allowed_roots:
                reference_issues += 1
                issues.append(
                    _issue(
                        "invalid_source_root",
                        f"{path}.source_refs",
                        f"{reference} is not an allowed upstream source for this module.",
                        severity="high",
                        blocking=True,
                    )
                )
                continue
            valid, _, evidence = _resolve_ref(reference, roots)
            if not valid:
                reference_issues += 1
                issues.append(
                    _issue(
                        "invalid_source_ref",
                        f"{path}.source_refs",
                        f"{reference} does not resolve to an upstream field.",
                        severity="high",
                        blocking=True,
                    )
                )
            elif evidence is not None:
                source_evidence.append(evidence)

        item_evidence = item.get("evidence")
        if item_evidence and source_evidence:
            downstream = InsightEvidence.model_validate(item_evidence)
            weakest_basis = min(BASIS_RANK[source.basis] for source in source_evidence)
            weakest_confidence = min(
                CONFIDENCE_RANK[source.confidence] for source in source_evidence
            )
            if (
                BASIS_RANK[downstream.basis] > weakest_basis
                or CONFIDENCE_RANK[downstream.confidence] > weakest_confidence
            ):
                evidence_issues += 1
                issues.append(
                    _issue(
                        "evidence_stronger_than_source",
                        f"{path}.evidence",
                        "Downstream evidence is stronger than at least one cited upstream source.",
                        severity="high",
                        blocking=True,
                    )
                )

        text = _item_text(item)
        if item_evidence:
            evidence = InsightEvidence.model_validate(item_evidence)
            risky_market_claim = MARKET_ASSERTION_PATTERN.search(text)
            unsupported_strength = UNSUPPORTED_STRENGTH_PATTERN.search(text)
            if evidence.basis == "explicit_brief" and (risky_market_claim or unsupported_strength):
                claim_issues += 1
                issues.append(
                    _issue(
                        "unsupported_explicit_market_claim",
                        path,
                        "This comparative or market claim is labeled as explicit brief evidence but is not directly established by the brief.",
                        severity="high",
                        blocking=True,
                    )
                )
            elif (risky_market_claim or unsupported_strength) and not HYPOTHESIS_MARKER.search(
                text
            ):
                claim_issues += 1
                issues.append(
                    _issue(
                        "unsupported_claim_language",
                        path,
                        "Use neutral or explicit hypothesis language for frequency, comparative, or causal wording.",
                    )
                )

    for path, item in _evidenced_user_items(user_data):
        evidence = InsightEvidence.model_validate(item["evidence"])
        text = _item_text(item)
        if evidence.basis == "explicit_brief" and MARKET_ASSERTION_PATTERN.search(text):
            claim_issues += 1
            issues.append(
                _issue(
                    "unsupported_explicit_market_claim",
                    path,
                    "The user-insight item introduces a market or alternative claim that is not explicit in the brief.",
                    severity="high",
                    blocking=True,
                )
            )

    primary_refs = value_proposition.primary_value.source_refs
    primary_roots = {reference.split(".", 1)[0] for reference in primary_refs}
    if not {"user_insight", "market_hypothesis"}.issubset(primary_roots):
        grounding_issues += 1
        issues.append(
            _issue(
                "primary_value_missing_decision_link",
                "value_proposition.primary_value.source_refs",
                "Primary value must cite both a user insight and a market hypothesis.",
                severity="high",
                blocking=True,
            )
        )

    segment_tokens = _tokens(user_insight.target_user.primary_segment)
    audience_tokens = _tokens(context.target_audience)
    if audience_tokens and not audience_tokens.intersection(segment_tokens):
        grounding_issues += 1
        issues.append(
            _issue(
                "target_user_drift",
                "user_insight.target_user.primary_segment",
                "The primary user no longer overlaps with the normalized target audience.",
                severity="high",
                blocking=True,
            )
        )
    if context.primary_goal != brief.business_goal:
        grounding_issues += 1
        issues.append(
            _issue(
                "business_goal_drift",
                "context.primary_goal",
                "The normalized business goal differs from the submitted brief.",
                severity="high",
                blocking=True,
            )
        )

    brief_tokens = _tokens(f"{brief.product_description} {context.brief_summary}")
    for index, reason in enumerate(value_proposition.reasons_to_believe):
        if reason.support_status != "brief_supported":
            continue
        capability_tokens = _tokens(reason.capability)
        overlap = capability_tokens.intersection(brief_tokens)
        if not any(ref.startswith("context.") for ref in reason.source_refs) or len(overlap) < 2:
            grounding_issues += 1
            issues.append(
                _issue(
                    "reason_to_believe_not_grounded",
                    f"value_proposition.reasons_to_believe.{index}",
                    "A brief-supported capability must cite context and materially overlap with the submitted product description.",
                    severity="high",
                    blocking=True,
                )
            )

    testability_issues = 0
    for index, priority in enumerate(market_hypothesis.validation_priorities):
        if not (
            MEASURABLE_SIGNAL.search(priority.pass_signal)
            and MEASURABLE_SIGNAL.search(priority.fail_signal)
        ):
            testability_issues += 1
            issues.append(
                _issue(
                    "validation_signal_not_measurable",
                    f"market_hypothesis.validation_priorities.{index}",
                    "Pass and fail signals should include an observable threshold, count, percentage, or time bound.",
                )
            )

    checks = [
        QualityCheck(
            code="structure_contract",
            label="Structure contract",
            status="passed",
            detail="All four strategy objects passed their typed structural contracts.",
        ),
        QualityCheck(
            code="reference_integrity",
            label="Reference integrity",
            status="warning" if reference_issues else "passed",
            detail=f"{reference_issues} invalid or downstream reference(s) found."
            if reference_issues
            else "Every source reference resolves to an allowed upstream field.",
        ),
        QualityCheck(
            code="evidence_inheritance",
            label="Evidence inheritance",
            status="warning" if evidence_issues else "passed",
            detail=f"{evidence_issues} item(s) claim stronger evidence than a cited source."
            if evidence_issues
            else "Downstream evidence does not exceed cited upstream evidence.",
        ),
        QualityCheck(
            code="market_claim_grounding",
            label="Market claim grounding",
            status="warning" if claim_issues else "passed",
            detail=(
                f"{claim_issues} market or comparative claim(s) need review."
                if claim_issues
                else f"{auto_revision_count} inferred claim(s) were reframed as explicit hypotheses before this check."
                if auto_revision_count
                else "No unsupported factual market or comparative claims were detected."
            ),
        ),
        QualityCheck(
            code="decision_continuity",
            label="Decision continuity",
            status="warning" if grounding_issues else "passed",
            detail=f"{grounding_issues} target, value, goal, or product-grounding issue(s) found."
            if grounding_issues
            else "Target user, goal, primary value, and product support remain connected.",
        ),
        QualityCheck(
            code="validation_testability",
            label="Validation testability",
            status="warning" if testability_issues else "passed",
            detail=f"{testability_issues} validation plan(s) need measurable pass and fail signals."
            if testability_issues
            else "Every validation priority has measurable pass and fail signals.",
        ),
    ]

    blocking_count = sum(issue.blocking for issue in issues)
    status = "review_required" if blocking_count else "passed_with_notes" if issues else "passed"
    return StrategyQualityReview(
        status=status,
        issue_count=len(issues),
        blocking_issue_count=blocking_count,
        auto_revision_count=auto_revision_count,
        checks=checks,
        issues=issues,
    )
