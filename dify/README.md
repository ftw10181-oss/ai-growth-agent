# Dify workspace

## Stable path: import the V0.2 DSL

1. Open Dify Studio.
2. Choose **Create from DSL file**.
3. Upload `workflow-v0.2.yml`.
4. Open each LLM node and select a model available in your workspace.
5. Confirm structured output remains enabled on both LLM nodes.
6. Run the sample in `../demo/sample-output/request.json`.
7. Publish the workflow and create its API key.

The DSL uses Dify app DSL `0.7.0` and a default OpenAI model reference. Dify may ask you to install or configure the OpenAI model provider. You may replace it with any chat model in your workspace that reliably supports structured output.

## Fallback path: build manually

If your Dify workspace cannot resolve the imported model provider, follow `workflow-v0.2.md`. The canvas, variable names, prompts, schemas, and end outputs must stay the same because the backend depends on that contract.

The reviewed `workflow-v0.1.yml` and its guide remain in the repository as the reproducible baseline used for the first 12-case evaluation.

## V0.3 development path

V0.3 is a separate candidate so the published V0.2 workflow remains stable during regression testing. Import `workflow-v0.3.yml` first; use the manual guide when the workspace cannot resolve its model provider.

1. Choose **Create from DSL file** and upload `workflow-v0.3.yml`.
2. Select a structured-output-capable model for all four LLM nodes.
3. If import fails, create a new workflow and follow `workflow-v0.3.md`.
4. Reuse the V0.2 Context Interpreter and User Insight contracts.
5. Confirm `context`, `user_insight`, `market_hypothesis`, and `value_proposition` are exposed at End.
6. Do not replace the production V0.2 application or key until the V0.3 regression gates pass.

## V0.5 research path

V0.5 is a separate research-backed candidate. It adds the official Tavily
Search Tool, deterministic source normalization, an evidence brief, and a
claim-citation map while retaining the V0.3 strategy modules.

1. Keep the published V0.3 application unchanged.
2. Create a separate workflow named `AI Growth Agent — V0.5`.
3. Install the official Tavily plugin from Dify Marketplace and configure its
   credential in Dify; never place the key in this repository.
4. Follow `workflow-v0.5.md` to build and test the canvas.
5. Use the V0.5 prompts, schemas, and deterministic source-normalizer Code node.
6. Connect a separate development API key only after provenance and citation
   tests pass.

## Source files

- `prompts/01-context-interpreter.md`
- `prompts/02-user-insight.md`
- `prompts/03-market-hypothesis.md`
- `prompts/04-value-proposition.md`
- `prompts/05-research-planner.md`
- `prompts/06-source-evaluator.md`
- `prompts/07-evidence-synthesizer.md`
- `prompts/08-claim-citation-mapper.md`
- `prompts/09-evidence-grounding-addendum.md`
- `schemas/context-interpreter.schema.json`
- `schemas/user-insight.schema.json`
- `schemas/market-hypothesis.schema.json`
- `schemas/value-proposition.schema.json`
- `schemas/research-plan.schema.json`
- `schemas/source-manifest.schema.json`
- `schemas/evidence-brief.schema.json`
- `schemas/claim-citations.schema.json`
- `code/normalize_search_results.py`

When changing a V0.2 prompt or schema, run `python dify/build_workflow_v02.py` to rebuild the importable DSL, then run the repository verification commands before committing.

When changing a V0.3 prompt or schema, run `python dify/build_workflow_v03.py` to rebuild `workflow-v0.3.yml` before verification.

V0.5 intentionally begins with the manual workflow guide. Generate an
importable DSL only after the Tavily node has been configured and exported from
the user's Dify workspace, because plugin identifiers and credential bindings
are workspace-specific.
