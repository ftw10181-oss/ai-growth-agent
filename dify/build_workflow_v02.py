"""Build the importable V0.2 Dify DSL from reviewed prompt and schema sources."""

import json
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parent


def main() -> None:
    workflow = yaml.safe_load((ROOT / "workflow-v0.1.yml").read_text(encoding="utf-8"))
    workflow["app"]["name"] = "AI Growth Agent — V0.2"
    workflow["app"]["description"] = (
        "Turn an overseas growth brief into evidence-aware, testable user hypotheses."
    )

    nodes = {node["id"]: node["data"] for node in workflow["workflow"]["graph"]["nodes"]}
    nodes["context_interpreter"]["prompt_template"][0]["text"] = (
        ROOT / "prompts" / "01-context-interpreter.md"
    ).read_text(encoding="utf-8")
    nodes["user_insight"]["prompt_template"][0]["text"] = (
        ROOT / "prompts" / "02-user-insight.md"
    ).read_text(encoding="utf-8")
    nodes["user_insight"]["structured_output"]["schema"] = json.loads(
        (ROOT / "schemas" / "user-insight.schema.json").read_text(encoding="utf-8")
    )
    nodes["user_insight"]["desc"] = (
        "Generate ranked hypotheses with evidence basis, confidence, and validation status."
    )

    (ROOT / "workflow-v0.2.yml").write_text(
        yaml.safe_dump(workflow, sort_keys=False, allow_unicode=True, width=1000),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
