# Product Thinking Notes

## The key product decision

This product starts with interpretation, not generation.

A generic assistant can generate personas from a sentence, but that hides ambiguity and encourages false confidence. AI Growth Agent first makes the brief legible: product category, market, audience, goal, stage, constraints, signals, and assumptions. The insight step then reasons from that shared context.

This improves three things:

1. Traceability — users can see what the analysis is based on.
2. Reusability — later modules can consume the same normalized context.
3. Trust — missing evidence becomes an explicit assumption instead of an invented fact.

## Why User Insight is the first module

Growth plans fail upstream. If the user, job, or scenario is vague, downstream channel and content recommendations merely scale the vagueness. User Insight also creates concrete next actions: interview questions, landing-page messages, and experiment hypotheses.

## Why the audience is narrow

V0.1 focuses on overseas growth for AI, SaaS, and consumer technology products. This is narrow enough for meaningful vocabulary and scenarios, but broad enough to demonstrate a reusable workflow. It also makes the portfolio story coherent: the product addresses a recognizable operating problem rather than showcasing prompt tricks.

## Hypotheses, not research claims

Without live sources, “market analysis” can easily become fabricated authority. V0.1 labels insights as hypotheses and provides confidence plus validation questions. Web research belongs in a later evidence-aware release with citations, recency, source quality, and conflict handling.

## Human–AI division of work

The AI is good at synthesis, reframing, and enumerating plausible alternatives. The human remains responsible for prioritization, field validation, ethical judgment, and commercial decisions. The interface supports that division by showing assumptions and research questions beside the output.

## Trade-offs

| Decision | Benefit | Cost |
|---|---|---|
| Two LLM nodes | Better traceability and reusable context | More latency and tokens |
| Structured JSON | Reliable UI and evaluation | Less expressive free-form prose |
| Mock mode | Zero-credential portfolio demo | Not representative of model variation |
| No database | Small attack surface and fast setup | No history or comparison yet |
| No web search | Honest positioning and simpler MVP | Insights require human validation |

## Evaluation approach

Create 10 briefs spanning AI hardware, SaaS, and consumer apps. A growth practitioner scores each item on specificity, relevance, internal consistency, testability, and unsupported-claim risk. Automated checks cover schema validity, required sections, item counts, and forbidden quantitative claims. Failed cases become regression examples for prompt revisions.

## Interview story

The project demonstrates the work of an AI product operator: scoping a real problem, choosing an orchestration boundary, designing prompts and schemas, exposing assumptions, planning evaluation, and shipping a reviewable end-to-end slice—not simply generating text with an LLM.

