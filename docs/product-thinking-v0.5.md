# Product Thinking — V0.5

## Why the version jumps from V0.3 to V0.5

V0.3 improved the depth of the strategy chain. V0.5 changes the source of
decision confidence. The product now has to plan research, retrieve changing
external information, expose provenance, handle conflict, and fail safely.
Those changes affect workflow design, data contracts, UI, evaluation, cost,
security, and the product promise; they are larger than a single-module V0.4.

## The product is not a search wrapper

A search wrapper optimizes for answers and links. AI Growth Agent optimizes for
a better growth decision. Search is useful only when it changes one of four
things:

- which user or scenario should be prioritized;
- which market or competitor assumption is supported or challenged;
- which value proposition is credible enough to test;
- which unknown should be investigated before spending budget.

For that reason, the Research Planner is upstream of search and the Evidence
Synthesizer is upstream of strategy. Raw search output never becomes the final
recommendation.

## Why research is bounded

An open-ended agent would appear more autonomous but would be harder to explain,
evaluate, price, and trust. V0.5 limits the workflow to five questions and ten
retained sources. The constraint makes latency, cost, citation coverage, and
failure behavior observable enough for a portfolio-grade product.

## Why citations are a separate map

V0.3 already uses `source_refs` to prove internal continuity between Context,
User Insight, Market Hypothesis, and Value Proposition. V0.5 keeps that contract
and adds a separate claim-citation map for external evidence.

This distinction prevents two common errors:

1. treating an upstream AI inference as external evidence;
2. coupling every strategy schema to one search provider's response format.

## Human–AI boundary

### AI may

- propose research questions;
- synthesize retrieved material;
- classify evidence status;
- explain strategic implications;
- propose validation priorities.

### Deterministic code must

- create source IDs;
- preserve the URLs returned by the tool;
- deduplicate and validate references;
- enforce evidence thresholds;
- surface conflicts and gaps;
- protect credentials, quota, and fallback behavior.

### A human must decide

- whether a source is suitable for a high-stakes decision;
- whether a contested finding blocks execution;
- whether the recommended growth wedge justifies budget;
- whether additional primary research is required.

## Recruiter-facing story

V0.5 demonstrates more than prompt construction. It shows that the builder can:

- translate a product risk into a system contract;
- design a research workflow around a real operating decision;
- separate model reasoning from deterministic control;
- make evidence, uncertainty, and failure visible in the interface;
- evaluate a changing AI system without pretending web results are deterministic;
- manage provider secrets, rate limits, caching, and graceful degradation.

## Honest product claim

Until user studies are completed, the project should claim that it **produces a
traceable research-backed strategy artifact**, not that it improves conversion,
reduces research time by a measured percentage, or replaces a professional
market researcher.

