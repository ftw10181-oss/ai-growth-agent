import json
from pathlib import Path

from app.models import BusinessGoal, GrowthBrief


CASES_PATH = Path(__file__).parents[2] / "evals" / "cases.json"


def load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]


def test_evaluation_cases_are_valid_unique_briefs() -> None:
    cases = load_cases()
    assert len(cases) >= 10
    assert len({case["id"] for case in cases}) == len(cases)
    for case in cases:
        GrowthBrief.model_validate(case["input"])
        assert case["focus"]


def test_evaluation_set_covers_every_business_goal() -> None:
    goals = {case["input"]["business_goal"] for case in load_cases()}
    assert goals == {goal.value for goal in BusinessGoal}


def test_evaluation_set_contains_boundary_cases() -> None:
    difficulties = {case["difficulty"] for case in load_cases()}
    assert {"sparse", "goal_conflict", "unfamiliar_domain"}.issubset(difficulties)
