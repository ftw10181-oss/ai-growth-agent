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

Without live sources, “market analysis” can easily become fabricated authority. V0.1 used cautious Prompt instructions, but its baseline showed that instructions alone did not reliably prevent inferred behavior from sounding factual. V0.2 turns evidence quality into a required output contract: every insight identifies its basis, confidence, validation status, and decision relevance. Web research belongs in a later release with citations, recency, source quality, and conflict handling.

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

Use the same 12 fixed briefs spanning six business goals and multiple product families. A reviewer scores each item on specificity, relevance, internal consistency, testability, and unsupported-claim risk. Automated checks cover schema validity, required sections, evidence consistency, item counts, and forbidden claims. Failed V0.1 cases become the unchanged regression set for V0.2.

## Why the quality gate and safe-wording revision are deterministic

Prompt instructions are probabilistic: a model can understand a rule and still violate it on a later run. V0.2.1 therefore applies two server-side steps after schema validation. First, a deterministic revision layer prefixes risky frequency, comparative, or causal wording with `Hypothesis to test —`; it preserves the original wording after that marker and records the number of revisions. Second, the quality gate evaluates the revised output.

This layer does not establish truth, remove substantive content, or invent supporting evidence. It changes the epistemic framing so an inference cannot be mistaken for a verified finding. Structural and evidence failures remain blocking. Research-question mismatches and any unresolved wording findings appear as non-blocking review notes, because they affect usefulness but do not mean the workflow failed.

## Interview story

The project demonstrates the work of an AI product operator: scoping a real problem, choosing an orchestration boundary, designing prompts and schemas, exposing assumptions, planning evaluation, and shipping a reviewable end-to-end slice—not simply generating text with an LLM.
