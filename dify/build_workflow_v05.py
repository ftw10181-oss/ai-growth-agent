"""Build the importable V0.5 Dify DSL from reviewed source files."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
GROUNDING_ADDENDUM = "09-evidence-grounding-addendum.md"
OPENAI_STRING_FORMATS = {
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


def _read_prompt(name: str) -> str:
    return (ROOT / "prompts" / name).read_text(encoding="utf-8")


def _read_schema(name: str) -> dict[str, Any]:
    schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
    return _openai_schema(schema)


def _openai_schema(value: Any) -> Any:
    """Return the strict Structured Outputs subset accepted by OpenAI.

    The repository schemas remain the authoritative validation contract. Dify's
    LLM nodes receive a projection without unsupported uniqueness enforcement or
    unsupported string formats; the backend quality gate enforces those rules.
    """

    if isinstance(value, list):
        return [_openai_schema(item) for item in value]
    if not isinstance(value, dict):
        return value

    projected: dict[str, Any] = {}
    for key, item in value.items():
        if key == "uniqueItems":
            continue
        if key == "format" and item not in OPENAI_STRING_FORMATS:
            continue
        projected[key] = _openai_schema(item)
    return projected


def _node_wrapper(data: dict[str, Any], *, node_id: str, x: int, y: int = 280) -> dict:
    return {
        "data": data,
        "height": 120,
        "id": node_id,
        "position": {"x": x, "y": y},
        "positionAbsolute": {"x": x, "y": y},
        "selected": False,
        "sourcePosition": "right",
        "targetPosition": "left",
        "type": "custom",
        "width": 260,
    }


def _llm_node(
    template: dict[str, Any],
    *,
    node_id: str,
    title: str,
    description: str,
    system_prompt: str,
    user_prompt: str,
    schema: dict[str, Any],
    temperature: float,
    x: int,
) -> dict[str, Any]:
    node = copy.deepcopy(template)
    node["id"] = node_id
    node["position"] = {"x": x, "y": 280}
    node["positionAbsolute"] = {"x": x, "y": 280}
    data = node["data"]
    data["title"] = title
    data["desc"] = description
    data["model"]["completion_params"] = {"temperature": temperature}
    data["prompt_template"] = [
        {"id": f"{node_id}-system", "role": "system", "text": system_prompt},
        {"id": f"{node_id}-user", "role": "user", "text": user_prompt},
    ]
    data["structured_output"]["schema"] = schema
    return node


def _edge(
    source: str,
    target: str,
    *,
    source_type: str,
    target_type: str,
    iteration_id: str | None = None,
) -> dict[str, Any]:
    in_iteration = iteration_id is not None
    data: dict[str, Any] = {
        "isInIteration": in_iteration,
        "isInLoop": False,
        "sourceType": source_type,
        "targetType": target_type,
    }
    if iteration_id:
        data["iteration_id"] = iteration_id
    return {
        "data": data,
        "id": f"{source}-source-{target}-target",
        "source": source,
        "sourceHandle": "source",
        "target": target,
        "targetHandle": "target",
        "type": "custom",
        "zIndex": 1002 if in_iteration else 0,
    }


def _iteration_nodes() -> list[dict[str, Any]]:
    iteration = _node_wrapper(
        {
            "desc": "Run at most five bounded Tavily searches in serial order.",
            "error_handle_mode": "continue-on-error",
            "flatten_output": True,
            "height": 310,
            "is_parallel": False,
            "iterator_input_type": "array[object]",
            "iterator_selector": [
                "research_planner",
                "structured_output",
                "questions",
            ],
            "output_selector": ["package_search_result", "result"],
            "output_type": "array[object]",
            "parallel_nums": 1,
            "selected": False,
            "startNodeType": "tool",
            "start_node_id": "research_iteration_start",
            "title": "Bounded Web Research",
            "type": "iteration",
            "width": 720,
        },
        node_id="research_iteration",
        x=1060,
        y=190,
    )
    iteration["height"] = 310
    iteration["width"] = 720
    iteration["zIndex"] = 1

    start = _node_wrapper(
        {
            "desc": "",
            "isInIteration": True,
            "selected": False,
            "title": "",
            "type": "iteration-start",
        },
        node_id="research_iteration_start",
        x=24,
        y=78,
    )
    start.update(
        {
            "draggable": False,
            "height": 48,
            "parentId": "research_iteration",
            "positionAbsolute": {"x": 1084, "y": 268},
            "selectable": False,
            "type": "custom-iteration-start",
            "width": 44,
            "zIndex": 1002,
        }
    )

    tool = _node_wrapper(
        {
            "desc": "Return structured JSON search results; generated answers are disabled.",
            "isInIteration": True,
            "iteration_id": "research_iteration",
            "is_team_authorization": True,
            "provider_id": "langgenius/tavily/tavily",
            "provider_name": "langgenius/tavily/tavily",
            "provider_type": "builtin",
            "selected": False,
            "title": "Tavily Search",
            "tool_configurations": {
                "auto_parameters": {"type": "constant", "value": False},
                "include_answer": {"type": "constant", "value": "false"},
                "include_favicon": {"type": "constant", "value": False},
                "include_image_descriptions": {
                    "type": "constant",
                    "value": False,
                },
                "include_images": {"type": "constant", "value": False},
                "include_raw_content": {"type": "constant", "value": "false"},
                "include_usage": {"type": "constant", "value": True},
                "max_results": {"type": "constant", "value": 5},
            },
            "tool_label": "Tavily Search",
            "tool_name": "tavily_search",
            "tool_node_version": "2",
            "tool_parameters": {
                "query": {
                    "type": "mixed",
                    "value": "{{#research_iteration.item.query#}}",
                },
                "search_depth": {"type": "constant", "value": "basic"},
                "time_range": {"type": "constant", "value": "not_specified"},
                "topic": {"type": "constant", "value": "general"},
            },
            "type": "tool",
        },
        node_id="tavily_search",
        x=100,
        y=95,
    )
    tool.update(
        {
            "extent": "parent",
            "parentId": "research_iteration",
            "positionAbsolute": {"x": 1160, "y": 285},
            "zIndex": 1002,
        }
    )

    package = _node_wrapper(
        {
            "code": (
                "def main(question: dict, raw_result=None) -> dict:\n"
                "    question = question if isinstance(question, dict) else {}\n"
                "    return {\n"
                "        'result': {\n"
                "            'query_id': question.get('question_id'),\n"
                "            'search_result': raw_result,\n"
                "        }\n"
                "    }\n"
            ),
            "code_language": "python3",
            "desc": "Bind each immutable question ID to its raw Tool JSON output.",
            "isInIteration": True,
            "iteration_id": "research_iteration",
            "outputs": {"result": {"children": None, "type": "object"}},
            "selected": False,
            "title": "Package Search Result",
            "type": "code",
            "variables": [
                {
                    "value_selector": ["research_iteration", "item"],
                    "variable": "question",
                },
                {"value_selector": ["tavily_search", "json"], "variable": "raw_result"},
            ],
        },
        node_id="package_search_result",
        x=405,
        y=95,
    )
    package.update(
        {
            "extent": "parent",
            "parentId": "research_iteration",
            "positionAbsolute": {"x": 1465, "y": 285},
            "zIndex": 1002,
        }
    )
    return [iteration, start, tool, package]


def _normalizer_node(x: int) -> dict[str, Any]:
    return _node_wrapper(
        {
            "code": (ROOT / "code" / "normalize_search_results.py").read_text(
                encoding="utf-8"
            ),
            "code_language": "python3",
            "desc": "Canonicalize URLs, deduplicate sources, and assign provenance IDs.",
            "outputs": {"source_manifest": {"children": None, "type": "object"}},
            "selected": False,
            "title": "Source Normalizer",
            "type": "code",
            "variables": [
                {
                    "value_selector": ["research_iteration", "output"],
                    "variable": "raw_results",
                },
                {
                    "value_selector": [
                        "research_planner",
                        "structured_output",
                        "questions",
                    ],
                    "variable": "query_ids",
                },
                {"value_selector": ["sys", "timestamp"], "variable": "researched_at"},
            ],
        },
        node_id="source_normalizer",
        x=x,
    )


def _evidence_gate_node(x: int) -> dict[str, Any]:
    return _node_wrapper(
        {
            "code": (ROOT / "code" / "validate_evidence_brief.py").read_text(
                encoding="utf-8"
            ),
            "code_language": "python3",
            "desc": (
                "Enforce source provenance, relevance, coverage, and confidence "
                "rules before strategy generation."
            ),
            "outputs": {
                "validated_evidence_brief": {"children": None, "type": "object"},
                "evidence_audit": {"children": None, "type": "object"},
            },
            "selected": False,
            "title": "Deterministic Evidence Gate",
            "type": "code",
            "variables": [
                {
                    "value_selector": [
                        "evidence_synthesizer",
                        "structured_output",
                    ],
                    "variable": "evidence_brief",
                },
                {
                    "value_selector": ["source_evaluator", "structured_output"],
                    "variable": "source_manifest",
                },
                {
                    "value_selector": ["research_planner", "structured_output"],
                    "variable": "research_plan",
                },
            ],
        },
        node_id="evidence_gate",
        x=x,
    )


def main() -> None:
    workflow = yaml.safe_load((ROOT / "workflow-v0.3.yml").read_text(encoding="utf-8"))
    workflow["app"]["name"] = "AI Growth Agent — V0.5"
    workflow["app"]["description"] = (
        "Turn an overseas growth brief into a bounded, evidence-backed strategy with live web sources."
    )

    graph = workflow["workflow"]["graph"]
    old_nodes = {node["id"]: node for node in graph["nodes"]}
    llm_template = old_nodes["user_insight"]

    context = copy.deepcopy(old_nodes["context_interpreter"])
    context["position"] = {"x": 380, "y": 280}
    context["positionAbsolute"] = {"x": 380, "y": 280}

    planner = _llm_node(
        llm_template,
        node_id="research_planner",
        title="Research Planner",
        description="Create three to five decision-focused web research questions.",
        system_prompt=_read_prompt("05-research-planner.md"),
        user_prompt=(
            "Normalized growth context:\n"
            "{{#context_interpreter.structured_output#}}"
        ),
        schema=_read_schema("research-plan.schema.json"),
        temperature=0.1,
        x=720,
    )

    normalizer = _normalizer_node(1900)
    evaluator = _llm_node(
        llm_template,
        node_id="source_evaluator",
        title="Source Evaluator",
        description="Classify source quality while preserving immutable provenance fields.",
        system_prompt=_read_prompt("06-source-evaluator.md"),
        user_prompt=(
            "Research plan:\n{{#research_planner.structured_output#}}\n\n"
            "Deterministic source manifest:\n{{#source_normalizer.source_manifest#}}"
        ),
        schema=_read_schema("source-manifest.schema.json"),
        temperature=0,
        x=2240,
    )
    synthesizer = _llm_node(
        llm_template,
        node_id="evidence_synthesizer",
        title="Evidence Synthesizer",
        description="Create bounded findings, contradictions, gaps, and implications.",
        system_prompt=_read_prompt("07-evidence-synthesizer.md"),
        user_prompt=(
            "Research plan:\n{{#research_planner.structured_output#}}\n\n"
            "Evaluated source manifest:\n{{#source_evaluator.structured_output#}}"
        ),
        schema=_read_schema("evidence-brief.schema.json"),
        temperature=0.1,
        x=2580,
    )
    evidence_gate = _evidence_gate_node(2920)

    addendum = _read_prompt(GROUNDING_ADDENDUM)
    user_insight = copy.deepcopy(old_nodes["user_insight"])
    user_insight["position"] = {"x": 3260, "y": 280}
    user_insight["positionAbsolute"] = {"x": 3260, "y": 280}
    user_insight["data"]["prompt_template"][0]["text"] = (
        _read_prompt("02-user-insight.md") + "\n\n" + addendum
    )
    user_insight["data"]["prompt_template"][1]["text"] = (
        "Normalized growth context:\n{{#context_interpreter.structured_output#}}\n\n"
        "Validated V0.5 evidence brief:\n"
        "{{#evidence_gate.validated_evidence_brief#}}"
    )
    user_insight["data"]["desc"] = "Generate evidence-aware, testable user hypotheses."

    market = copy.deepcopy(old_nodes["market_hypothesis"])
    market["position"] = {"x": 3600, "y": 280}
    market["positionAbsolute"] = {"x": 3600, "y": 280}
    market["data"]["prompt_template"][0]["text"] = (
        _read_prompt("03-market-hypothesis.md") + "\n\n" + addendum
    )
    market["data"]["prompt_template"][1]["text"] = (
        "Normalized context:\n{{#context_interpreter.structured_output#}}\n\n"
        "Evidence-aware user insight:\n{{#user_insight.structured_output#}}\n\n"
        "Validated V0.5 evidence brief:\n"
        "{{#evidence_gate.validated_evidence_brief#}}"
    )

    value = copy.deepcopy(old_nodes["value_proposition"])
    value["position"] = {"x": 3940, "y": 280}
    value["positionAbsolute"] = {"x": 3940, "y": 280}
    value["data"]["prompt_template"][0]["text"] = (
        _read_prompt("04-value-proposition.md") + "\n\n" + addendum
    )
    value["data"]["prompt_template"][1]["text"] = (
        "Normalized context:\n{{#context_interpreter.structured_output#}}\n\n"
        "Evidence-aware user insight:\n{{#user_insight.structured_output#}}\n\n"
        "Market hypothesis:\n{{#market_hypothesis.structured_output#}}\n\n"
        "Validated V0.5 evidence brief:\n"
        "{{#evidence_gate.validated_evidence_brief#}}"
    )

    citations = _llm_node(
        llm_template,
        node_id="claim_citation_mapper",
        title="Claim Citation Mapper",
        description="Map material strategy paths to evidence findings.",
        system_prompt=_read_prompt("08-claim-citation-mapper.md"),
        user_prompt=(
            "Validated evidence brief:\n"
            "{{#evidence_gate.validated_evidence_brief#}}\n\n"
            "User insight:\n{{#user_insight.structured_output#}}\n\n"
            "Market hypothesis:\n{{#market_hypothesis.structured_output#}}\n\n"
            "Value proposition:\n{{#value_proposition.structured_output#}}"
        ),
        schema=_read_schema("claim-citations.schema.json"),
        temperature=0,
        x=4280,
    )

    end = copy.deepcopy(old_nodes["end"])
    end["position"] = {"x": 4620, "y": 280}
    end["positionAbsolute"] = {"x": 4620, "y": 280}
    end["data"]["desc"] = "Return research provenance, evidence, strategy, and claim citations."
    end["data"]["outputs"] = [
        {
            "value_selector": ["context_interpreter", "structured_output"],
            "value_type": "object",
            "variable": "context",
        },
        {
            "value_selector": ["research_planner", "structured_output"],
            "value_type": "object",
            "variable": "research_plan",
        },
        {
            "value_selector": ["source_evaluator", "structured_output"],
            "value_type": "object",
            "variable": "source_manifest",
        },
        {
            "value_selector": ["evidence_gate", "validated_evidence_brief"],
            "value_type": "object",
            "variable": "evidence_brief",
        },
        {
            "value_selector": ["evidence_gate", "evidence_audit"],
            "value_type": "object",
            "variable": "evidence_audit",
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
        {
            "value_selector": ["claim_citation_mapper", "structured_output"],
            "value_type": "object",
            "variable": "claim_citations",
        },
    ]

    iteration, iteration_start, tavily, package = _iteration_nodes()
    graph["nodes"] = [
        copy.deepcopy(old_nodes["start"]),
        context,
        planner,
        iteration,
        iteration_start,
        tavily,
        package,
        normalizer,
        evaluator,
        synthesizer,
        evidence_gate,
        user_insight,
        market,
        value,
        citations,
        end,
    ]
    graph["edges"] = [
        _edge("start", "context_interpreter", source_type="start", target_type="llm"),
        _edge(
            "context_interpreter",
            "research_planner",
            source_type="llm",
            target_type="llm",
        ),
        _edge(
            "research_planner",
            "research_iteration",
            source_type="llm",
            target_type="iteration",
        ),
        _edge(
            "research_iteration_start",
            "tavily_search",
            source_type="iteration-start",
            target_type="tool",
            iteration_id="research_iteration",
        ),
        _edge(
            "tavily_search",
            "package_search_result",
            source_type="tool",
            target_type="code",
            iteration_id="research_iteration",
        ),
        _edge(
            "research_iteration",
            "source_normalizer",
            source_type="iteration",
            target_type="code",
        ),
        _edge(
            "source_normalizer",
            "source_evaluator",
            source_type="code",
            target_type="llm",
        ),
        _edge(
            "source_evaluator",
            "evidence_synthesizer",
            source_type="llm",
            target_type="llm",
        ),
        _edge(
            "evidence_synthesizer",
            "evidence_gate",
            source_type="llm",
            target_type="code",
        ),
        _edge(
            "evidence_gate",
            "user_insight",
            source_type="code",
            target_type="llm",
        ),
        _edge(
            "user_insight",
            "market_hypothesis",
            source_type="llm",
            target_type="llm",
        ),
        _edge(
            "market_hypothesis",
            "value_proposition",
            source_type="llm",
            target_type="llm",
        ),
        _edge(
            "value_proposition",
            "claim_citation_mapper",
            source_type="llm",
            target_type="llm",
        ),
        _edge(
            "claim_citation_mapper",
            "end",
            source_type="llm",
            target_type="end",
        ),
    ]
    graph["viewport"] = {"x": 10, "y": 120, "zoom": 0.35}

    (ROOT / "workflow-v0.5.yml").write_text(
        yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True, width=1000),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
