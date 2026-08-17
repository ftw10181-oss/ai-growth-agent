import csv
import json
from pathlib import Path

from app.models import GrowthBrief, UserInsightResponse


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "evals" / "results" / "baseline-v0.1"


def test_published_baseline_passes_contract_and_hard_structure_gates():
    case_set = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))

    for case in case_set["cases"]:
        brief = GrowthBrief.model_validate(case["input"])
        response = UserInsightResponse.model_validate_json(
            (RESULTS / f"{case['id']}.json").read_text(encoding="utf-8")
        )

        assert response.context.primary_goal == brief.business_goal
        assert {item.dimension for item in response.user_insight.jobs_to_be_done} == {
            "functional",
            "emotional",
            "social",
        }
        for section in (
            response.user_insight.jobs_to_be_done,
            response.user_insight.pain_points,
            response.user_insight.purchase_motivations,
            response.user_insight.adoption_barriers,
            response.user_insight.typical_scenarios,
            response.user_insight.research_questions,
        ):
            assert 3 <= len(section) <= 5


def test_published_baseline_summary_and_scorecard_are_complete():
    summary = json.loads((RESULTS / "run-summary.json").read_text(encoding="utf-8"))
    with (RESULTS / "scorecard.csv").open(encoding="utf-8") as handle:
        scorecard = list(csv.DictReader(handle))

    assert summary["case_count"] == 12
    assert summary["success_count"] == 12
    assert summary["failure_count"] == 0
    assert len(scorecard) == 12
    assert {row["case_id"] for row in scorecard} == {
        case["case_id"] for case in summary["cases"]
    }
