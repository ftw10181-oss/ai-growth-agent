from pathlib import Path

import yaml

from app.models import (
    ClaimCitationMap,
    EvidenceBrief,
    MarketHypothesis,
    NormalizedContext,
    ResearchPlan,
    SourceManifest,
    UserInsight,
    UserInsightV01,
    ValueProposition,
)


DSL_PATH = Path(__file__).parents[2] / "dify" / "workflow-v0.1.yml"
DSL_V02_PATH = Path(__file__).parents[2] / "dify" / "workflow-v0.2.yml"
DSL_V03_PATH = Path(__file__).parents[2] / "dify" / "workflow-v0.3.yml"
DSL_V05_PATH = Path(__file__).parents[2] / "dify" / "workflow-v0.5.yml"


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
    assert set(insight_schema["required"]) == set(UserInsightV01.model_json_schema()["required"])

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


def test_v02_dify_dsl_enforces_evidence_contract() -> None:
    dsl = yaml.safe_load(DSL_V02_PATH.read_text())
    nodes = {node["id"]: node["data"] for node in dsl["workflow"]["graph"]["nodes"]}
    schema = nodes["user_insight"]["structured_output"]["schema"]

    assert dsl["app"]["name"] == "AI Growth Agent — V0.2"
    assert set(schema["required"]) == set(UserInsight.model_json_schema()["required"])
    assert set(schema["$defs"]["insightItem"]["required"]) == {
        "insight",
        "why_it_matters",
        "decision_relevance",
        "evidence",
    }
    assert schema["properties"]["pain_points"]["minItems"] == 2
    assert schema["properties"]["typical_scenarios"]["minItems"] == 2

    source_prompt = (
        Path(__file__).parents[2] / "dify" / "prompts" / "02-user-insight.md"
    ).read_text()
    assert nodes["user_insight"]["prompt_template"][0]["text"] == source_prompt
    assert "Each of `jobs_to_be_done`" in source_prompt
    assert "Think about the most recent time" in source_prompt
    assert "final mechanical check" in source_prompt


def test_v03_dify_dsl_adds_traceable_strategy_modules() -> None:
    dsl = yaml.safe_load(DSL_V03_PATH.read_text())
    graph = dsl["workflow"]["graph"]
    nodes = {node["id"]: node["data"] for node in graph["nodes"]}

    assert dsl["app"]["name"] == "AI Growth Agent — V0.3"
    assert set(nodes) == {
        "start",
        "context_interpreter",
        "user_insight",
        "market_hypothesis",
        "value_proposition",
        "end",
    }

    market_schema = nodes["market_hypothesis"]["structured_output"]["schema"]
    value_schema = nodes["value_proposition"]["structured_output"]["schema"]
    assert "growth_wedge" in market_schema["required"]
    assert set(market_schema["required"]) == set(MarketHypothesis.model_json_schema()["required"])
    assert market_schema["properties"]["validation_priorities"]["minItems"] == 3
    assert "primary_value" in value_schema["required"]
    assert set(value_schema["required"]) == set(ValueProposition.model_json_schema()["required"])
    assert value_schema["properties"]["message_pillars"]["minItems"] == 3

    end_outputs = {
        item["variable"]: item["value_selector"] for item in nodes["end"]["outputs"]
    }
    assert end_outputs == {
        "context": ["context_interpreter", "structured_output"],
        "user_insight": ["user_insight", "structured_output"],
        "market_hypothesis": ["market_hypothesis", "structured_output"],
        "value_proposition": ["value_proposition", "structured_output"],
    }

    edge_pairs = {(edge["source"], edge["target"]) for edge in graph["edges"]}
    assert edge_pairs == {
        ("start", "context_interpreter"),
        ("context_interpreter", "user_insight"),
        ("user_insight", "market_hypothesis"),
        ("market_hypothesis", "value_proposition"),
        ("value_proposition", "end"),
    }

    market_prompt = (
        Path(__file__).parents[2] / "dify" / "prompts" / "03-market-hypothesis.md"
    ).read_text()
    value_prompt = (
        Path(__file__).parents[2] / "dify" / "prompts" / "04-value-proposition.md"
    ).read_text()
    assert nodes["market_hypothesis"]["prompt_template"][0]["text"] == market_prompt
    assert nodes["value_proposition"]["prompt_template"][0]["text"] == value_prompt


def test_v05_dify_dsl_adds_bounded_research_and_citation_contracts() -> None:
    dsl = yaml.safe_load(DSL_V05_PATH.read_text())
    graph = dsl["workflow"]["graph"]
    nodes = {node["id"]: node["data"] for node in graph["nodes"]}

    assert dsl["app"]["name"] == "AI Growth Agent — V0.5"
    assert set(nodes) == {
        "start",
        "context_interpreter",
        "research_planner",
        "research_iteration",
        "research_iteration_start",
        "tavily_search",
        "package_search_result",
        "source_normalizer",
        "source_evaluator",
        "evidence_synthesizer",
        "evidence_gate",
        "user_insight",
        "market_hypothesis",
        "value_proposition",
        "claim_citation_mapper",
        "end",
    }

    iteration = nodes["research_iteration"]
    assert iteration["iterator_input_type"] == "array[object]"
    assert iteration["output_type"] == "array[object]"
    assert iteration["is_parallel"] is False
    assert iteration["error_handle_mode"] == "continue-on-error"

    tool = nodes["tavily_search"]
    assert tool["provider_id"] == "langgenius/tavily/tavily"
    assert tool["tool_name"] == "tavily_search"
    assert tool["tool_node_version"] == "2"
    assert tool["tool_configurations"]["max_results"] == {
        "type": "constant",
        "value": 5,
    }
    assert tool["tool_configurations"]["include_answer"] == {
        "type": "constant",
        "value": "false",
    }
    assert all(
        set(configuration) == {"type", "value"}
        for configuration in tool["tool_configurations"].values()
    )
    assert tool["tool_parameters"]["search_depth"]["value"] == "basic"

    package_code = nodes["package_search_result"]["code"]
    assert "'search_result': raw_result" in package_code
    assert "isinstance(raw_result, dict)" not in package_code

    planner_prompt = nodes["research_planner"]["prompt_template"][0]["text"]
    assert "RQ-001" in planner_prompt
    assert "literally include the target market value" in planner_prompt

    evaluator_prompt = nodes["source_evaluator"]["prompt_template"][0]["text"]
    assert "freshness` must be `unknown" in evaluator_prompt
    assert "is `vendor`, not `independent_secondary`" in evaluator_prompt

    synthesizer_prompt = nodes["evidence_synthesizer"]["prompt_template"][0]["text"]
    assert "otherwise it is not eligible" in synthesizer_prompt
    assert "answered_question_count" in synthesizer_prompt

    evidence_gate = nodes["evidence_gate"]
    assert evidence_gate["type"] == "code"
    assert "MIN_RELEVANCE = 0.5" in evidence_gate["code"]
    assert set(evidence_gate["outputs"]) == {
        "validated_evidence_brief",
        "evidence_audit",
    }

    schemas = {
        "research_planner": ResearchPlan,
        "source_evaluator": SourceManifest,
        "evidence_synthesizer": EvidenceBrief,
        "claim_citation_mapper": ClaimCitationMap,
    }
    for node_id, model in schemas.items():
        schema = nodes[node_id]["structured_output"]["schema"]
        assert set(schema["required"]) == set(model.model_json_schema()["required"])

        def walk_schema(value):
            if isinstance(value, dict):
                assert "uniqueItems" not in value
                if "format" in value:
                    assert value["format"] in {
                        "date-time",
                        "time",
                        "date",
                        "duration",
                        "email",
                        "hostname",
                        "ipv4",
                        "ipv6",
                        "uuid",
                    }
                for child in value.values():
                    walk_schema(child)
            elif isinstance(value, list):
                for child in value:
                    walk_schema(child)

        walk_schema(schema)

    search_limit_properties = nodes["research_planner"]["structured_output"][
        "schema"
    ]["properties"]["search_limits"]["properties"]
    assert search_limit_properties["max_queries"] == {"type": "integer", "const": 5}
    assert search_limit_properties["max_retained_sources"] == {
        "type": "integer",
        "const": 10,
    }

    end_outputs = {
        item["variable"]: item["value_selector"] for item in nodes["end"]["outputs"]
    }
    assert end_outputs == {
        "context": ["context_interpreter", "structured_output"],
        "research_plan": ["research_planner", "structured_output"],
        "source_manifest": ["source_evaluator", "structured_output"],
        "evidence_brief": ["evidence_gate", "validated_evidence_brief"],
        "evidence_audit": ["evidence_gate", "evidence_audit"],
        "user_insight": ["user_insight", "structured_output"],
        "market_hypothesis": ["market_hypothesis", "structured_output"],
        "value_proposition": ["value_proposition", "structured_output"],
        "claim_citations": ["claim_citation_mapper", "structured_output"],
    }

    grounding = (Path(__file__).parents[2] / "dify" / "prompts" / "09-evidence-grounding-addendum.md").read_text()
    for node_id in ("user_insight", "market_hypothesis", "value_proposition"):
        assert grounding in nodes[node_id]["prompt_template"][0]["text"]
