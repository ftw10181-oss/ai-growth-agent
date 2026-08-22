"""Build the importable V0.3 Dify DSL from reviewed prompt and schema sources."""

import copy
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent


def _read_prompt(name: str) -> str:
    return (ROOT / "prompts" / name).read_text(encoding="utf-8")


def _read_schema(name: str) -> dict:
    return json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))


def _edge(source: str, target: str) -> dict:
    return {
        "data": {
            "isInIteration": False,
            "isInLoop": False,
            "sourceType": "llm",
            "targetType": "end" if target == "end" else "llm",
        },
        "id": f"{source.replace('_', '-')}-source-{target.replace('_', '-')}-target",
        "source": source,
        "sourceHandle": "source",
        "target": target,
        "targetHandle": "target",
        "type": "custom",
        "zIndex": 0,
    }


def _llm_node(template: dict, *, node_id: str, title: str, description: str,
              system_prompt: str, user_prompt: str, schema: dict, x: int) -> dict:
    node = copy.deepcopy(template)
    node["id"] = node_id
    node["position"]["x"] = x
    node["positionAbsolute"]["x"] = x
    data = node["data"]
    data["title"] = title
    data["desc"] = description
    data["prompt_template"] = [
        {"id": f"{node_id}-system", "role": "system", "text": system_prompt},
        {"id": f"{node_id}-user", "role": "user", "text": user_prompt},
    ]
    data["structured_output"]["schema"] = schema
    return node


def main() -> None:
    workflow = yaml.safe_load((ROOT / "workflow-v0.2.yml").read_text(encoding="utf-8"))
    workflow["app"]["name"] = "AI Growth Agent — V0.3"
    workflow["app"]["description"] = (
        "Turn an overseas growth brief into traceable user, market, and value hypotheses."
    )

    graph = workflow["workflow"]["graph"]
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    insight_template = nodes_by_id["user_insight"]

    market_node = _llm_node(
        insight_template,
        node_id="market_hypothesis",
        title="Market Hypothesis",
        description="Identify a narrow growth wedge, market risks, and validation priorities.",
        system_prompt=_read_prompt("03-market-hypothesis.md"),
        user_prompt=(
            "Normalized context:\n{{#context_interpreter.structured_output#}}\n\n"
            "Evidence-aware user insight:\n{{#user_insight.structured_output#}}"
        ),
        schema=_read_schema("market-hypothesis.schema.json"),
        x=1060,
    )
    value_node = _llm_node(
        insight_template,
        node_id="value_proposition",
        title="Value Proposition",
        description="Create grounded value, positioning, objections, and message tests.",
        system_prompt=_read_prompt("04-value-proposition.md"),
        user_prompt=(
            "Normalized context:\n{{#context_interpreter.structured_output#}}\n\n"
            "Evidence-aware user insight:\n{{#user_insight.structured_output#}}\n\n"
            "Market hypothesis:\n{{#market_hypothesis.structured_output#}}"
        ),
        schema=_read_schema("value-proposition.schema.json"),
        x=1400,
    )

    end_node = nodes_by_id["end"]
    end_node["position"]["x"] = 1740
    end_node["positionAbsolute"]["x"] = 1740
    end_node["data"]["desc"] = "Return context, user, market, and value hypothesis objects."
    end_node["data"]["outputs"] = [
        {
            "value_selector": ["context_interpreter", "structured_output"],
            "value_type": "object",
            "variable": "context",
        },
        {
            "value_selector": ["user_insight", "structured_output"],
            "value_type": "object",
            "variable": "user_insight",
        },
        {
            "value_selector": ["market_hypothesis", "structured_output"],
            "value_type": "object",
            "variable": "market_hypothesis",
        },
        {
            "value_selector": ["value_proposition", "structured_output"],
            "value_type": "object",
            "variable": "value_proposition",
        },
    ]

    graph["nodes"] = [
        nodes_by_id["start"],
        nodes_by_id["context_interpreter"],
        nodes_by_id["user_insight"],
        market_node,
        value_node,
        end_node,
    ]
    graph["edges"] = [
        edge
        for edge in graph["edges"]
        if not (edge["source"] == "user_insight" and edge["target"] == "end")
    ] + [
        _edge("user_insight", "market_hypothesis"),
        _edge("market_hypothesis", "value_proposition"),
        _edge("value_proposition", "end"),
    ]
    graph["viewport"] = {"x": 20, "y": 120, "zoom": 0.65}

    (ROOT / "workflow-v0.3.yml").write_text(
        yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True, width=1000),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
