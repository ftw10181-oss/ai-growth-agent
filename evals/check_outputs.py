"""Validate saved AI Growth Agent evaluation outputs without calling an API."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.models import GrowthBrief, UserInsightResponse  # noqa: E402


RISK_PATTERNS = {
    "quantitative_claim": re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|percent|million|billion)\b", re.I),
    "implied_research": re.compile(r"\b(?:research shows|studies show|data shows|according to research)\b", re.I),
    "unsupported_frequency": re.compile(r"\b(?:many|most|often|frequently|significantly)\b", re.I),
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from flatten_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from flatten_strings(item)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path, help="Directory containing <case-id>.json outputs")
    args = parser.parse_args()

    case_data = load_json(ROOT / "evals" / "cases.json")
    cases = {case["id"]: case for case in case_data["cases"]}
    failures = []

    for case_id, case in cases.items():
        output_path = args.output_dir / f"{case_id}.json"
        if not output_path.exists():
            failures.append(f"{case_id}: missing output file")
            continue

        try:
            brief = GrowthBrief.model_validate(case["input"])
            response = UserInsightResponse.model_validate(load_json(output_path))
        except Exception as exc:  # validation details belong in evaluation logs
            failures.append(f"{case_id}: contract failure: {exc}")
            continue

        if response.context.primary_goal != brief.business_goal:
            failures.append(f"{case_id}: primary goal mismatch")

        combined = "\n".join(flatten_strings(response.model_dump(mode="json")))
        for label, pattern in RISK_PATTERNS.items():
            if pattern.search(combined):
                failures.append(f"{case_id}: review flag: {label}")

    if failures:
        print("\n".join(failures))
        return 1

    print(f"Validated {len(cases)} evaluation outputs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
