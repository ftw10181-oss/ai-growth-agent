# Dify Workflow Build Guide — V0.5

V0.5 adds bounded live web research and external evidence traceability while
preserving the V0.3 strategy contract.

## Canvas

```text
[Start]
   ↓
[Context Interpreter]
   ↓
[Research Planner]
   ↓
[Iteration: research questions]
   └─ [Tavily Search Tool]
   ↓
[Source Normalizer — Code]
   ↓
[Source Evaluator — LLM]
   ↓
[Evidence Synthesizer — LLM]
   ↓
[User Insight — LLM]
   ↓
[Market Hypothesis — LLM]
   ↓
[Value Proposition — LLM]
   ↓
[Claim Citation Mapper — LLM]
   ↓
[End]

Server after Dify:
[URL + Citation Integrity] → [Evidence Quality Gate] → [V0.3 Strategy Gate]
```

## 1. Create a separate application

Create a new Dify Workflow named `AI Growth Agent — V0.5`. Do not overwrite the
published V0.3 application. V0.3 is the safe fallback until all V0.5 release
gates pass.

Keep the same six Start fields and business-goal options documented in
`workflow-v0.3.md`.

## 2. Install and configure web search

In Dify Plugin Marketplace, install the official `Tavily` Tool plugin. Add the
Tavily credential under Tools → Tavily → Authentication.

V0.5 uses only `Tavily Search`. Do not enable autonomous Research, Crawl, Map,
or Extract in the first release.

The official plugin returns a JSON object whose `results` entries expose title,
URL, content, score, and an optional publication date. The Source Normalizer
must consume the JSON Tool output, not the formatted text message.

## 3. Context Interpreter

Reuse:

- Prompt: `prompts/01-context-interpreter.md`
- Schema: `schemas/context-interpreter.schema.json`
- Output: `context`

## 4. Research Planner

- Node: LLM
- Temperature: `0.1`
- Prompt: `prompts/05-research-planner.md`
- Schema: `schemas/research-plan.schema.json`
- Input: Context Interpreter structured output
- Output: `research_plan`

The node must return three to five questions. The schema always advertises a
maximum of five queries and ten retained sources even when fewer questions are
generated.

## 5. Query iteration

Create an Iteration node over `research_plan.questions`.

Inside it, add `Tavily Search` with these fixed parameters:

| Parameter | V0.5 value |
|---|---|
| `query` | Current iteration item / `query` |
| `search_depth` | `basic` |
| `topic` | `general` |
| `max_results` | `5` |
| `include_answer` | `false` |
| `include_raw_content` | `false` |
| `include_images` | `false` |
| `include_image_descriptions` | `false` |
| `include_favicon` | `false` |
| `include_usage` | `true` |
| `auto_parameters` | `false` |

For the first release, keep `time_range=not_specified`. The planner's recency
preference is evaluated downstream because strict time filtering can erase
useful primary sources with unknown dates.

Expose the Tool JSON object as the iteration output. Do not expose Tavily's
generated `answer` field to later strategy nodes.

## 6. Source Normalizer

- Node: Code / Python
- Source: `code/normalize_search_results.py`
- Inputs:
  - `raw_results`: Iteration aggregate JSON outputs
  - `query_ids`: ordered Research Planner question IDs
  - `researched_at`: workflow start timestamp in ISO 8601 form
  - `failed_query_ids`: query IDs reported as failed, or an empty list
- Output: `source_manifest`

This node is the provenance boundary. It:

- accepts only HTTPS URLs returned by the Tool;
- removes common tracking parameters;
- deduplicates canonical URLs;
- assigns `SRC-###` IDs;
- preserves query IDs and retrieval time;
- caps retained sources at ten.

No LLM may edit source IDs or URLs after this node.

## 7. Source Evaluator

- Node: LLM
- Temperature: `0`
- Prompt: `prompts/06-source-evaluator.md`
- Schema: `schemas/source-manifest.schema.json`
- Inputs: Research Plan and Source Normalizer output
- Output: `source_manifest_evaluated`

The evaluator may complete publisher, source class, relevance, freshness, and
limitations. It must preserve IDs, URLs, query IDs, titles, snippets, and
retrieval timestamps exactly. The server will compare both manifests and block
any provenance mutation.

## 8. Evidence Synthesizer

- Node: LLM
- Temperature: `0.1`
- Prompt: `prompts/07-evidence-synthesizer.md`
- Schema: `schemas/evidence-brief.schema.json`
- Inputs: Research Plan and evaluated Source Manifest
- Output: `evidence_brief`

The evidence brief must preserve contradictions and return at least one research
gap. A weak result becomes `insufficient`; it is not omitted.

## 9. Strategy chain

Run the V0.3 modules sequentially:

1. User Insight
2. Market Hypothesis
3. Value Proposition

For each node, use its existing V0.3 prompt and append
`prompts/09-evidence-grounding-addendum.md`. Add the Evidence Brief to the user
message input.

The module schemas remain unchanged. Their `source_refs` continue to prove
internal decision continuity; they are not external citations.

## 10. Claim Citation Mapper

- Node: LLM
- Temperature: `0`
- Prompt: `prompts/08-claim-citation-mapper.md`
- Schema: `schemas/claim-citations.schema.json`
- Inputs: Evidence Brief plus all three final strategy objects
- Output: `claim_citations`

This node creates the explicit bridge between external evidence and final
strategy paths. It may not modify either side.

## 11. End node

Expose these structured outputs:

| Output | Source |
|---|---|
| `context` | Context Interpreter |
| `research_plan` | Research Planner |
| `source_manifest` | Source Evaluator |
| `evidence_brief` | Evidence Synthesizer |
| `user_insight` | User Insight |
| `market_hypothesis` | Market Hypothesis |
| `value_proposition` | Value Proposition |
| `claim_citations` | Claim Citation Mapper |

## 12. Test sequence

1. **Search provenance** — every final source URL must occur in the Tavily JSON
   output and remain unchanged after evaluation.
2. **Duplicate URL** — return the same URL for two queries and confirm a single
   source contains both query IDs.
3. **Weak evidence** — use only vendor/community results and confirm confidence
   does not become high.
4. **Conflict** — provide two relevant sources with opposing signals and confirm
   the finding remains contested.
5. **Partial failure** — fail one query and confirm useful sources remain with
   `research_status=partial`.
6. **Full failure** — fail every query and confirm the product returns a clearly
   labeled V0.3 fallback.
7. **Citation integrity** — introduce an unknown source or finding ID and confirm
   the server blocks the response.
8. **Regression** — run the existing fixed cases and preserve every V0.3 contract.

## 13. Publish policy

Publish V0.5 with a separate Dify application and API key. First connect it to a
development endpoint. Promote it to the public Sites demo only after frozen
fixture tests, live smoke tests, and human evidence review pass.

