# Dify Workflow Build Guide — V0.3

V0.3 extends the evidence-aware V0.2 canvas with Market Hypothesis and Value Proposition. It keeps the existing six-field input and upstream schemas stable.

## Canvas

```text
[Start]
   ↓
[Context Interpreter — structured output]
   ↓
[User Insight — structured output]
   ↓
[Market Hypothesis — structured output]
   ↓
[Value Proposition — structured output]
   ↓
[End]

Server after Dify:
[Safe-wording Revision] → [Cross-module Quality Gate] → [Strategy Summary]
```

The deterministic revision and quality layers remain outside the model workflow so the model cannot grade or silently approve its own output.

## 1. Application

Create a new Dify Workflow named `AI Growth Agent — V0.3`. Do not overwrite the published V0.2 application until the fixed regression set passes.

Use a model with native structured output. Begin with temperature `0.2` for all four LLM nodes.

## 2. Start node

Keep the V0.2 input contract exactly:

| Label | Variable | Type | Required | Limit / options |
|---|---|---|---|---|
| Product | `product` | Short Text | Yes | 120 |
| Product Description | `product_description` | Paragraph | Yes | 2,000 |
| Target Market | `target_market` | Short Text | Yes | 120 |
| Target Audience | `target_audience` | Paragraph | Yes | 500 |
| Business Goal | `business_goal` | Select | Yes | Brand Awareness; User Acquisition; Conversion; Community Growth; Product Launch; Retention |
| Additional Context | `additional_context` | Paragraph | No | 2,000 |

## 3. Context Interpreter

Use the existing configuration:

- Prompt: `prompts/01-context-interpreter.md`
- Schema: `schemas/context-interpreter.schema.json`
- Output alias: `context`

User message:

```text
Product: {{#start.product#}}
Product description: {{#start.product_description#}}
Target market: {{#start.target_market#}}
Target audience: {{#start.target_audience#}}
Business goal: {{#start.business_goal#}}
Additional context: {{#start.additional_context#}}
```

## 4. User Insight

Use the existing V0.2 configuration:

- Prompt: `prompts/02-user-insight.md`
- Schema: `schemas/user-insight.schema.json`
- Output alias: `user_insight`

User message:

```text
Normalized growth context:
{{#context_interpreter.structured_output#}}
```

## 5. Market Hypothesis

- Node type: LLM
- Title: `Market Hypothesis`
- Prompt: `prompts/03-market-hypothesis.md`
- Schema: `schemas/market-hypothesis.schema.json`
- Inputs: Context Interpreter and User Insight structured outputs
- Output alias: `market_hypothesis`

User message:

```text
Normalized context:
{{#context_interpreter.structured_output#}}

Evidence-aware user insight:
{{#user_insight.structured_output#}}
```

Expected behavior:

- Chooses one narrow growth wedge
- Treats alternatives and user behavior as hypotheses unless explicit
- Returns at least three observable validation priorities
- Uses only real upstream paths in `source_refs`
- Makes no market-size, market-growth, competitor-performance, or willingness-to-pay claim

## 6. Value Proposition

- Node type: LLM
- Title: `Value Proposition`
- Prompt: `prompts/04-value-proposition.md`
- Schema: `schemas/value-proposition.schema.json`
- Inputs: Context Interpreter, User Insight, and Market Hypothesis structured outputs
- Output alias: `value_proposition`

User message:

```text
Normalized context:
{{#context_interpreter.structured_output#}}

Evidence-aware user insight:
{{#user_insight.structured_output#}}

Market hypothesis:
{{#market_hypothesis.structured_output#}}
```

Expected behavior:

- Selects one primary value connected to a primary JTBD or pain and the growth wedge
- Preserves functional, emotional, and social value as separate dimensions
- Uses only supplied product capabilities as reasons to believe
- Returns message-test directions rather than campaign copy
- Uses only real upstream paths in `source_refs`

## 7. End node

Expose four object outputs:

| Output name | Source |
|---|---|
| `context` | Context Interpreter / `structured_output` |
| `user_insight` | User Insight / `structured_output` |
| `market_hypothesis` | Market Hypothesis / `structured_output` |
| `value_proposition` | Value Proposition / `structured_output` |

The server may accept JSON-encoded strings from Dify but must parse and validate every object before returning a public response.

## 8. Test order

### Contract test

Run the existing translation-earbuds request. Confirm that all four outputs are objects and validate against their schemas.

### Traceability test

Resolve every `source_ref` against the exact End-node output. Any missing path is a blocking failure.

### Product-grounding test

Use a brief with very few product capabilities. Confirm that `reasons_to_believe` does not add accuracy, privacy, offline use, integrations, performance, or price claims.

### Unfamiliar-domain test

Use an unfamiliar product category. Confirm that market statements remain hypotheses and contain no statistics, named competitors, citations, or fabricated trends.

### Regression test

Run all 12 fixed V0.1/V0.2 cases. Compare execution success, schema compliance, business-goal consistency, source-reference validity, latency, token use, and human content scores.

## 9. Publish policy

Publish V0.3 as a separate Dify application and key. Connect it first to a versioned development API. Promote it to the public demo only after all release gates in `docs/PRD.md` pass.
