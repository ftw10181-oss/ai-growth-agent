"""Validate saved AI Growth Agent evaluation outputs without calling an API."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import GrowthBrief, UserInsightResponse, UserInsightResponseV01  # noqa: E402


RISK_PATTERNS = {
    "quantitative_claim": re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|percent|million|billion)\b", re.I),
    "implied_research": re.compile(r"\b(?:research shows|studies show|data shows|according to research)\b", re.I),
    "unsupported_frequency": re.compile(r"\b(?:many|most|often|frequently|significantly)\b", re.I),
    "unsupported_causality": re.compile(
        r"\b(?:leads? to|results? in|directly impacts?|improves?|increases?|decreases?|enhances?)\b",
        re.I,
    ),
}

HYPOTHESIS_MARKERS = re.compile(r"\b(?:hypothesis to test|may|could)\b", re.I)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_strings(value, path=()):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from flatten_strings(item, (*path, str(index)))
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from flatten_strings(item, (*path, key))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path, help="Directory containing <case-id>.json outputs")
    args = parser.parse_args()

    case_data = load_json(ROOT / "evals" / "cases.json")
    cases = {case["id"]: case for case in case_data["cases"]}
    response_contract = (
        UserInsightResponseV01 if "v0.1" in args.output_dir.name else UserInsightResponse
    )
    failures = []
    review_flags = []

    for case_id, case in cases.items():
        output_path = args.output_dir / f"{case_id}.json"
        if not output_path.exists():
            failures.append(f"{case_id}: missing output file")
            continue

        try:
            brief = GrowthBrief.model_validate(case["input"])
            response = response_contract.model_validate(load_json(output_path))
        except Exception as exc:  # validation details belong in evaluation logs
            failures.append(f"{case_id}: contract failure: {exc}")
            continue

        if response.context.primary_goal != brief.business_goal:
            failures.append(f"{case_id}: primary goal mismatch")

        generated_insights = response.user_insight.model_dump(mode="json")
        for path, text in flatten_strings(generated_insights):
            # Questions and explicit assumptions are already framed for validation.
            if path and path[0] in {"research_questions", "assumptions_to_validate"}:
                continue
            for label, pattern in RISK_PATTERNS.items():
                if pattern.search(text) and not (
                    label == "unsupported_causality" and HYPOTHESIS_MARKERS.search(text)
                ):
                    review_flags.append(
                        f"{case_id}: review flag: {label} at user_insight.{'.'.join(path)}"
                    )

    if failures:
        print("\n".join(failures))
        return 1

    print(f"Validated {len(cases)} evaluation outputs: no contract or goal failures.")
    if review_flags:
        print("\n".join(review_flags))
        print(f"Review required: {len(review_flags)} possible unsupported-claim phrases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
