# Dify workspace

## Recommended path: import the DSL

1. Open Dify Studio.
2. Choose **Create from DSL file**.
3. Upload `workflow-v0.1.yml`.
4. Open each LLM node and select a model available in your workspace.
5. Confirm structured output remains enabled on both LLM nodes.
6. Run the sample in `../demo/sample-output/request.json`.
7. Publish the workflow and create its API key.

The DSL uses Dify app DSL `0.7.0` and a default OpenAI model reference. Dify may ask you to install or configure the OpenAI model provider. You may replace it with any chat model in your workspace that reliably supports structured output.

## Fallback path: build manually

If your Dify workspace cannot resolve the imported model provider, follow `workflow-v0.1.md`. The canvas, variable names, prompts, schemas, and end outputs must stay the same because the backend depends on that contract.

## Source files

- `prompts/01-context-interpreter.md`
- `prompts/02-user-insight.md`
- `schemas/context-interpreter.schema.json`
- `schemas/user-insight.schema.json`

When changing a prompt or schema, update the matching content embedded in `workflow-v0.1.yml` and run the repository verification commands before committing.

