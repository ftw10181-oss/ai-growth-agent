import re

from .models import QualityCheck, QualityIssue, QualityReview, UserInsight


RESEARCH_PATTERNS = (
    re.compile(r"^think about the most recent time\b", re.IGNORECASE),
    re.compile(r"^what do you use today\b", re.IGNORECASE),
    re.compile(r"^what evidence or result would you need\b", re.IGNORECASE),
)

RISK_PATTERNS = {
    "unsupported_frequency": re.compile(
        r"\b(?:many|most|often|frequently|significantly)\b", re.IGNORECASE
    ),
    "unsupported_causality": re.compile(
        r"\b(?:leads? to|results? in|directly impacts?|improves?|increases?|"
        r"decreases?|enhances?|faster|better)\b",
        re.IGNORECASE,
    ),
}

HYPOTHESIS_MARKERS = re.compile(r"\b(?:hypothesis to test|may|could)\b", re.IGNORECASE)


def _reviewable_strings(insight: UserInsight):
    yield "target_user.primary_segment", insight.target_user.primary_segment
    yield "target_user.rationale", insight.target_user.rationale

    for section_name in (
        "jobs_to_be_done",
        "pain_points",
        "purchase_motivations",
        "adoption_barriers",
        "typical_scenarios",
    ):
        for index, item in enumerate(getattr(insight, section_name)):
            content_field = "job" if section_name == "jobs_to_be_done" else "insight"
            yield f"{section_name}.{index}.{content_field}", getattr(item, content_field)
            yield f"{section_name}.{index}.why_it_matters", item.why_it_matters


def normalize_claim_language(insight: UserInsight) -> tuple[UserInsight, int]:
    """Reframe unsupported claim wording as an explicit hypothesis before review."""
    payload = insight.model_dump()
    revisions = 0

    def reframe(text: str) -> str:
        nonlocal revisions
        has_risk = any(pattern.search(text) for pattern in RISK_PATTERNS.values())
        if has_risk and not HYPOTHESIS_MARKERS.search(text):
            revisions += 1
            return f"Hypothesis to test — {text}"
        return text

    target_user = payload["target_user"]
    target_user["rationale"] = reframe(target_user["rationale"])

    for section_name in (
        "jobs_to_be_done",
        "pain_points",
        "purchase_motivations",
        "adoption_barriers",
        "typical_scenarios",
    ):
        content_field = "job" if section_name == "jobs_to_be_done" else "insight"
        for item in payload[section_name]:
            item[content_field] = reframe(item[content_field])
            item["why_it_matters"] = reframe(item["why_it_matters"])

    return UserInsight.model_validate(payload), revisions


def evaluate_quality(insight: UserInsight, auto_revision_count: int = 0) -> QualityReview:
    """Run deterministic checks after the model output passes the hard schema."""
    issues: list[QualityIssue] = []

    for index, (question, pattern) in enumerate(
        zip(insight.research_questions[:3], RESEARCH_PATTERNS)
    ):
        if not pattern.search(question):
            issues.append(
                QualityIssue(
                    code="research_question_pattern",
                    path=f"research_questions.{index}",
                    message=(
                        "Rewrite this question using the required behavior-first "
                        f"pattern for position {index + 1}."
                    ),
                )
            )

    for path, text in _reviewable_strings(insight):
        for code, pattern in RISK_PATTERNS.items():
            if pattern.search(text) and not HYPOTHESIS_MARKERS.search(text):
                issues.append(
                    QualityIssue(
                        code=code,
                        path=path,
                        message=(
                            "Review unsupported frequency, comparative, or causal wording; "
                            "use neutral or explicit hypothesis language."
                        ),
                    )
                )

    research_issues = [issue for issue in issues if issue.code == "research_question_pattern"]
    wording_issues = [issue for issue in issues if issue.code != "research_question_pattern"]
    checks = [
        QualityCheck(
            code="structure_contract",
            label="Structure contract",
            status="passed",
            detail="Required sections, item counts, JTBD dimensions, and primary priorities passed.",
        ),
        QualityCheck(
            code="evidence_contract",
            label="Evidence contract",
            status="passed",
            detail="Evidence basis, confidence, and validation status are internally consistent.",
        ),
        QualityCheck(
            code="research_question_patterns",
            label="Research question patterns",
            status="warning" if research_issues else "passed",
            detail=(
                f"{len(research_issues)} behavior-first question pattern(s) need review."
                if research_issues
                else "The first three questions cover recent behavior, current workaround, and proof threshold."
            ),
        ),
        QualityCheck(
            code="claim_language",
            label="Claim language",
            status="warning" if wording_issues else "passed",
            detail=(
                f"{len(wording_issues)} potentially unsupported phrase(s) need human review."
                if wording_issues
                else (
                    f"{auto_revision_count} high-risk phrase(s) were reframed as explicit hypotheses before this check."
                    if auto_revision_count
                    else "No unsupported frequency, comparative, or causal phrasing was detected."
                )
            ),
        ),
    ]

    hard_issue_codes = {"structure_contract", "evidence_contract"}
    has_hard_issue = any(issue.code in hard_issue_codes for issue in issues)
    status = "review_required" if has_hard_issue else "passed_with_notes" if issues else "passed"

    return QualityReview(
        status=status,
        issue_count=len(issues),
        auto_revision_count=auto_revision_count,
        checks=checks,
        issues=issues,
    )
