# AI Growth Agent V0.1 — Live Baseline Report

## Executive summary

AI Growth Agent V0.1 completed all 12 fixed evaluation briefs through the published Dify workflow. Every response passed the JSON contract, preserved the submitted business goal, included functional, emotional, and social JTBD dimensions, and stayed within the required section sizes.

The baseline demonstrates reliable workflow execution and strong brief relevance. It also exposes the main content-quality gap for V0.2: inferred user behavior is not always labeled as a hypothesis. Eight of 12 responses contain at least one frequency or magnitude phrase that requires human review.

This is a **single-reviewer internal baseline**, not user research or proof of business impact.

## Run facts

| Measure | Result |
|---|---:|
| Fixed cases | 12 |
| Successful workflow runs | 12 / 12 (100%) |
| JSON contract pass | 12 / 12 (100%) |
| Business-goal consistency pass | 12 / 12 (100%) |
| JTBD dimension coverage pass | 12 / 12 (100%) |
| Required item-count pass | 12 / 12 (100%) |
| Median end-to-end latency | 21.5 s |
| Mean end-to-end latency | 25.1 s |
| Total model tokens | 35,371 |
| Mean tokens per case | 2,948 |

The slowest case took 65.1 seconds. The other 11 completed in 32.2 seconds or less.

## Human rubric results

| Dimension | Mean score (1–5) |
|---|---:|
| Specificity | 3.75 |
| Relevance | 4.58 |
| Testability | 3.75 |
| Internal consistency | 4.00 |
| Unsupported-claim safety | 2.67 |
| **Overall** | **3.75** |

Two of 12 cases met the complete V0.1 publish threshold. The other cases failed the threshold because unsupported-claim safety was below 4, not because of schema or workflow failures.

## What worked

- The workflow handled six business goals and six product families without contract failures.
- The goal-conflict case correctly kept `Conversion` as the primary goal while exposing the conflicting awareness request as an assumption.
- The sparse-input case still produced a complete response, making missing evidence visible through assumptions and medium confidence.
- The industrial-AI case converted operational constraints—line stoppage, pilot risk, and missing case studies—into concrete adoption barriers and interview questions.
- All 12 outputs generated research questions that can seed customer interviews.

## What needs improvement

### 1. Hypotheses sometimes sound like research findings

Examples include statements that users “often” experience a problem or that a feature can “significantly” improve an outcome. These may be reasonable hypotheses, but the current wording gives them more certainty than the input supports.

### 2. Sparse briefs invite generic filler

When context is limited, the model completes all sections but introduces familiar SaaS assumptions such as security concerns, switching resistance, and learning-curve anxiety. V0.2 should reduce output volume or lower confidence when evidence is sparse.

### 3. Some secondary motivations dilute the decision

Guest impressions, thought leadership, and community recognition occasionally appear before more immediate functional needs. Future prompts should rank insights by confidence and decision relevance.

### 4. Latency has a long tail

Median latency was 21.5 seconds, while one run reached 65.1 seconds. Before broader use, the product should add timeout messaging, retry telemetry, and a visible progress state.

## V0.2 decision

The next prompt iteration should:

1. require hypothesis labels for every inferred pain, motivation, barrier, and scenario;
2. ban unqualified frequency, magnitude, comparative, and causal language;
3. assign an evidence basis and confidence level to each insight;
4. rank insights by decision relevance instead of always filling five slots;
5. reduce section size when the brief does not support specific claims.

The same 12 cases should then be rerun unchanged. V0.2 succeeds only if contract reliability remains 100%, unsupported-claim safety reaches at least 4.0, and the overall single-reviewer score reaches at least 4.0.

## Method and limitations

- Run date: 17 August 2026 (UTC)
- Workflow: published Dify V0.1 workflow
- Prompt version: V0.1
- Scoring: one internal reviewer using `evals/rubric.md`
- Inputs: synthetic briefs, not customer-submitted data
- No external market research or browsing was used by the workflow
- No participant usability sessions have been completed
- Scores indicate output quality under this test set only; they do not establish acquisition, conversion, retention, or revenue impact

Raw outputs, the run summary, and the completed scorecard are stored in this directory for reproducibility.
