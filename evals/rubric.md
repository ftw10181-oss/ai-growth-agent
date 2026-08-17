# AI Growth Agent V0.1 — Evaluation Rubric

## Purpose

This rubric measures whether an output is useful for growth discovery. It does not reward polished prose by itself.

Score each dimension from 1 to 5. Reviewers should score the output without seeing who or which prompt version produced it.

## Hard gates

An output cannot pass when any of these conditions is true:

- The response fails the public JSON contract.
- `primary_goal` conflicts with the submitted business goal.
- JTBD does not include functional, emotional, and social dimensions.
- A required section contains fewer than three or more than five items.
- The output presents an invented statistic, market size, user quote, competitor fact, research finding, or citation as evidence.

## Scored dimensions

### 1. Specificity

| Score | Definition |
|---:|---|
| 1 | Generic advice that could apply to almost any product or audience. |
| 2 | Mentions the category but lacks a concrete trigger, workaround, or situation. |
| 3 | Includes some product-specific details but several items remain broad. |
| 4 | Most items connect a concrete situation, friction, and consequence. |
| 5 | Every major item is situationally specific and easy to distinguish from a generic template. |

### 2. Relevance

| Score | Definition |
|---:|---|
| 1 | Conflicts with or ignores the product, audience, market, or goal. |
| 2 | Uses the brief superficially and introduces distracting assumptions. |
| 3 | Generally aligned, with some weak or secondary items. |
| 4 | Strong alignment across nearly all sections. |
| 5 | Every section clearly supports the submitted business goal and decision context. |

### 3. Testability

| Score | Definition |
|---:|---|
| 1 | Statements are abstract and cannot guide research or an experiment. |
| 2 | A few ideas could be tested after substantial rewriting. |
| 3 | At least half of the output can inform an interview or message test. |
| 4 | Most items suggest an observable behavior, threshold, or decision. |
| 5 | The output can directly seed interview questions, message hypotheses, and experiment criteria. |

### 4. Internal consistency

| Score | Definition |
|---:|---|
| 1 | Major contradictions exist between context, target user, jobs, and barriers. |
| 2 | Several sections repeat or undermine one another. |
| 3 | Mostly consistent, with minor repetition or drift. |
| 4 | Clear logic from context through research questions. |
| 5 | Every section is distinct, mutually reinforcing, and traceable to the normalized context. |

### 5. Unsupported-claim safety

| Score | Definition |
|---:|---|
| 1 | Multiple unsupported facts or quantitative claims are presented as evidence. |
| 2 | Strong frequency, magnitude, or market claims appear without evidence. |
| 3 | Claims are mostly cautious, but some certainty or implied evidence remains. |
| 4 | Unverified claims are consistently framed as hypotheses. |
| 5 | Facts, assumptions, confidence, and validation questions are clearly separated throughout. |

## Pass criteria

- All hard gates pass.
- Mean human score is at least 4.0.
- No scored dimension is below 3.
- Unsupported-claim safety is at least 4.
- At least 70% of individual insight items are rated “specific enough to test.”

## Reviewer notes

- Score the content, not the visual design.
- Do not infer facts that are absent from the brief.
- Mark repeated ideas even when the wording changes.
- Record one strongest item, one weakest item, and one recommended revision.
- Do not convert small samples into broad product-impact claims.
