from pathlib import Path

import yaml

from app.models import NormalizedContext, UserInsight


DSL_PATH = Path(__file__).parents[2] / "dify" / "workflow-v0.1.yml"


def test_dify_dsl_matches_public_contract() -> None:
    dsl = yaml.safe_load(DSL_PATH.read_text())

    assert dsl["kind"] == "app"
    assert dsl["version"] == "0.7.0"
    assert dsl["app"]["mode"] == "workflow"

    graph = dsl["workflow"]["graph"]
    nodes = {node["id"]: node["data"] for node in graph["nodes"]}
    assert set(nodes) == {"start", "context_interpreter", "user_insight", "end"}

    start_variables = [item["variable"] for item in nodes["start"]["variables"]]
    assert start_variables == [
        "product",
        "product_description",
        "target_market",
        "target_audience",
        "business_goal",
        "additional_context",
    ]

    context_schema = nodes["context_interpreter"]["structured_output"]["schema"]
    insight_schema = nodes["user_insight"]["structured_output"]["schema"]
    assert nodes["context_interpreter"]["structured_output_enabled"] is True
    assert nodes["user_insight"]["structured_output_enabled"] is True
    assert set(context_schema["required"]) == set(NormalizedContext.model_json_schema()["required"])
    assert set(insight_schema["required"]) == set(UserInsight.model_json_schema()["required"])

    end_outputs = {
        item["variable"]: item["value_selector"] for item in nodes["end"]["outputs"]
    }
    assert end_outputs == {
        "context": ["context_interpreter", "structured_output"],
        "user_insight": ["user_insight", "structured_output"],
    }

    edge_pairs = {(edge["source"], edge["target"]) for edge in graph["edges"]}
    assert edge_pairs == {
        ("start", "context_interpreter"),
        ("context_interpreter", "user_insight"),
        ("user_insight", "end"),
    }

