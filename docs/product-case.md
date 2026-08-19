# Using AI Agent to Transform Overseas User Feedback into Growth Insights

> A product case study for the [AI Growth Agent](https://github.com/ftw10181-oss/ai-growth-agent) project.
> It explains the problem the product exists for, how the current architecture addresses it, and where it goes next.
> See the [Live Demo](../README.md#live-demo) and the [README](../README.md) for the technical surface.

---

## Background

Growth teams working on overseas markets are not short of signals — they are short of time to make sense of them. Feedback arrives from many places at once:

- User feedback from onboarding surveys and support tickets
- Community discussions on Reddit, forums, Discord, and X
- App store reviews and rating comments
- Market signals: competitor launches, pricing changes, regional promotions

A typical research pass means opening a dozen tabs, reading long threads, copying quotes into a spreadsheet, and discussing what it all means. By the time a summary is written, the team has already made most decisions without it — or the research starts over for the next market, audience, or product line.

The core need is not more data. It is a way to turn scattered, unstructured signals into **structured, verifiable, decision-ready insight** — fast enough to keep up with how growth teams actually work.

---

## Problem

Manual analysis of overseas user feedback fails on three axes.

**Time consuming.** Collecting and synthesizing feedback from multiple channels takes days to weeks. The synthesis step — reading everything, grouping it, judging what matters — is the bottleneck, and it does not get cheaper with volume.

**Hard to validate.** A human-written summary carries no audit trail. When a report says "users struggle with setup," nobody can tell whether that came from ten reviews, one angry tweet, or the author's assumption. The same problem gets worse with AI: a raw LLM answer is fluent, confident, and unverifiable — it cannot tell the reader which part is grounded in input and which part is invented.

**Difficult to scale.** Every new market, new audience, or new product line restarts the process from zero. Insights produced in one research pass do not automatically transfer or accumulate, so the organization never builds a reusable understanding of its users.

These three problems share a root cause: the pipeline between raw feedback and growth insight treats **generation** as the goal, when the real goal is **trust**.

---

## Solution

AI Growth Agent restructures the pipeline around that goal. Instead of one prompt producing one block of text, the system inserts explicit reasoning, evidence, and evaluation layers:

```
Input (Growth Brief + Audience + Goal)
   ↓
Agent Reasoning          — typed schema: jobs, pain points, motivations,
                           barriers, recommendations, assumptions
   ↓
Evidence Validation     — every item tagged: basis (explicit_brief /
                           inferred_from_context / hypothesis), confidence
                           (high / medium / low), validation_status
   ↓
Confidence Evaluation   — per-section confidence + overall confidence,
                           computed from the evidence metadata
   ↓
Growth Insight Report   — typed report, recommendations, research questions,
                           assumptions to check
```

Four mechanisms carry the design:

1. **A typed output contract.** The LLM is asked to populate a Pydantic `InsightResponse` schema — not to write prose. Sections like Jobs to be Done, Pain Points, Purchase Motivations, Adoption Barriers, Recommendations, and Assumptions are first-class fields, so the report cannot drift into unstructured text.

2. **Evidence metadata on every claim.** Each item carries `evidence.basis` — stated in the brief, inferred from context, or a hypothesis that still needs testing — plus `evidence.confidence` and `validation_status`. Recommendations are tagged with `decision_relevance` (`primary` / `supporting`). A reader can tell, at a glance, which block is grounded and which block needs a human.

3. **An offline evaluation contract.** `evals/check_outputs.py` replays 12 frozen cases against the schema and asserts structural invariants: every `recommendation` traces to a `pain_point`, every `hypothesis` surfaces as a `research_question`, assumptions are self-contained. It runs in CI on every commit, with no live LLM calls — so a change to the prompt or parser cannot silently degrade output quality.

4. **A pluggable backend.** The same `/api/analyze` contract runs in `APP_MODE=mock` (no external services) or `APP_MODE=dify` (real LLM via a Dify workflow), which keeps the product testable during development and configurable in production.

---

## Example Scenario

> **Note on method.** The scenario below uses a fictional product to demonstrate how the system works. It shows the *method*, not a claimed business result — the numbers, quotes, and conclusions are illustrative and must not be read as real market data.

**Setup.** A growth team for **AI Translation Earbuds** — real-time translation earbuds that let two people speak their own languages — is planning a US entry. The brief:

```
Product:              AI Translation Earbuds
What does it do:      Real-time AI translation earbuds that let two people
                      speak their own languages naturally
Target market:        United States
Target audience:      Frequent international business travelers
Business goal:        User Acquisition
Additional context:   Entering the US market; test Reddit and TikTok.
                      Competing with Pocketalk-style devices.
```

**What the report produces.** The team gets a structured report instead of a paragraph. A condensed excerpt:

| Section | Example item | Evidence tag |
| --- | --- | --- |
| Jobs to be done | "Keep a business meeting flowing when both sides don't share a language" | `explicit_brief` — high |
| Pain point | "Carrying a dedicated device is fine for trips, too heavy for daily carry" | `inferred_from_context` — medium |
| Pain point | "Latency and accuracy in live conversation are the make-or-break moment" | `hypothesis` — low |
| Recommendation | "Position around the meeting use case, not the traveler's whole trip" | `primary` — links to the meeting JTBD |
| Recommendation | "Validate latency sensitivity with a 10-user usability pass before paid ads" | `Validate first` — links to the latency hypothesis |
| Research question | "Does the target audience already own Pocketalk-style devices, and why do they stop using them?" | — |
| Assumption | "Business travelers in the US routinely attend meetings with non-English speakers" | needs checking |

**How a reviewer reads it.** The evidence tags do the work:

- The meeting-focused JTBD is marked `explicit_brief` — it came from the input, so it is safe to build on.
- The daily-carry pain point is `inferred_from_context` — reasonable, but worth one round of validation.
- The latency sensitivity is a `hypothesis` — the report *requires* it to surface as a research question, so the team does not mistake it for a finding.

The report does not claim to know which of these is true. It tells the team **what is grounded, what is inferred, and what to validate next** — which is exactly what a growth team needs before spending budget on a campaign.

---

## Product Value

**Better decision support.** By separating grounded claims from hypotheses, the report tells a team *where* it can act today and *where* it must validate first. The `primary` / `Validate first` split on recommendations is a direct map from insight to next action, which shortens the distance between research and decision.

**More reliable AI output.** Reliability here is structural, not rhetorical. Every claim carries a basis, every hypothesis is forced into a research question, and an offline evaluation contract fails CI when invariants break. The system is designed so that an untrustworthy output is *detectable* — the team can see exactly which items are speculation and which are supported.

**Structured growth insights.** A typed `InsightResponse` means every report has the same shape: the same sections, the same evidence fields, the same traceability. That makes reports comparable across markets and products, which is the precondition for building a reusable understanding of users instead of restarting from zero every time.

---

## Future Improvements

**Community feedback integration.** Today the input is a written brief. The natural next step is ingesting community sources directly — Reddit threads, forum posts, Discord logs — and summarizing them as evidence-bearing input, so the report can cite *where* a signal came from instead of relying on the user to paste it.

**App review analysis.** App store reviews are the highest-volume, lowest-latency source of user feedback. Connecting review feeds to the same pipeline would let a team monitor pain point emergence over time and see whether a new release shifted sentiment — all within the existing evidence and confidence framework.

**Experiment recommendation.** The report currently ends at "validate this first." Closing the loop means turning validated hypotheses into concrete experiment proposals — audience, channel, message, success metric — so the pipeline runs from raw feedback all the way to a testable growth experiment.
