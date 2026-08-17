# Dify Workflow Build Guide — V0.1

This is the manual fallback canvas specification. Import `workflow-v0.1.yml` first; use this guide when your workspace cannot resolve the DSL's default model provider. After selecting your actual model and publishing, you may export the workspace-resolved app DSL as `dify/export.yml`.

## Canvas

```text
[Start]
   ↓
[Context Interpreter — LLM, structured output]
   ↓
[User Insight — LLM, structured output]
   ↓
[End]
```

## 1. Create the application

In Dify Studio choose **Create from blank → Workflow** and name it `AI Growth Agent — V0.1`.

Use a model that supports native structured output. Start with temperature `0.2`; consistency matters more than creative variation.

## 2. Start node

Add these user input fields exactly. The variable names must match the backend payload.

| Label | Variable | Type | Required | Limit / options |
|---|---|---|---|---|
| Product | `product` | Short Text | Yes | 120 |
| Product Description | `product_description` | Paragraph | Yes | 2,000 |
| Target Market | `target_market` | Short Text | Yes | 120 |
| Target Audience | `target_audience` | Paragraph | Yes | 500 |
| Business Goal | `business_goal` | Select | Yes | Brand Awareness; User Acquisition; Conversion; Community Growth; Product Launch; Retention |
| Additional Context | `additional_context` | Paragraph | No | 2,000 |

## 3. Context Interpreter node

- Node type: LLM
- Title: `Context Interpreter`
- System prompt: paste `prompts/01-context-interpreter.md`
- Input variables: all Start variables
- Structured output: enabled
- Output schema: import `schemas/context-interpreter.schema.json`
- Expected variable: `structured_output`
- Rename/reference downstream as: `context`

Map variables into the user message:

```text
Product: {{#start.product#}}
Product description: {{#start.product_description#}}
Target market: {{#start.target_market#}}
Target audience: {{#start.target_audience#}}
Business goal: {{#start.business_goal#}}
Additional context: {{#start.additional_context#}}
```

## 4. User Insight node

- Node type: LLM
- Title: `User Insight`
- System prompt: paste `prompts/02-user-insight.md`
- Input: Context Interpreter `structured_output`
- Structured output: enabled
- Output schema: import `schemas/user-insight.schema.json`
- Expected variable: `structured_output`
- Rename/reference at End as: `user_insight`

User message:

```text
Normalized growth context:
{{#context_interpreter.structured_output#}}
```

## 5. End node

Expose two object outputs:

| Output name | Source |
|---|---|
| `context` | Context Interpreter / `structured_output` |
| `user_insight` | User Insight / `structured_output` |

The backend also accepts these values if Dify returns them as JSON-encoded strings.

## 6. Test cases

### Happy path

Use `demo/sample-output/request.json`. Confirm that both outputs are objects and all arrays meet schema minimums.

### Sparse context

Remove `additional_context`. The workflow must still succeed and add missing commercial context to `assumptions`.

### Safety check

Use an unfamiliar product and market. Confirm that the response contains no fabricated market size, adoption rate, user quote, competitor claim, or citation.

## 7. Publish and connect

Publish the workflow, create its API key, and configure the backend environment. Dify’s published Workflow API uses a blocking request from the backend; keep the key server-side. Re-publish after prompt changes.
