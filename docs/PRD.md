# Product Requirements Document — V0.1

## 1. Product definition

AI Growth Agent is an AI-assisted growth intelligence product for overseas growth operators. It converts a loosely written product brief into a structured set of user hypotheses and next-step research directions.

V0.1 is deliberately narrower than a general “growth copilot.” It proves one valuable vertical slice: interpreting context and generating useful user insight.

## 2. Problem

Overseas growth work often begins with incomplete information spread across product notes, market assumptions, and stakeholder messages. Operators spend time restating this context before they can decide whom to target, which pain to test, or which scenario to prioritize.

Generic AI writing tools skip that reasoning layer and jump to copy. The result may sound polished while being strategically weak and difficult to validate.

## 3. Target user

Primary user: a growth or product-operations professional responsible for an AI, SaaS, or consumer technology product entering or expanding in an overseas market.

Typical roles:

- Overseas Growth Operator
- Growth Manager
- Product Operations Manager
- International Marketing Manager
- Early-stage AI founder

## 4. Job to be done

When I receive a new product-growth brief, help me turn incomplete context into clear user hypotheses so I can plan interviews, messaging tests, and acquisition experiments without starting from a blank page.

## 5. Scope

### In scope

- Six input fields: product, description, market, audience, goal, optional context
- Input validation and normalization
- Explicit assumptions and ambiguities
- User Insight output: target user, JTBD, pain points, purchase motivations, adoption barriers, and scenarios
- Structured JSON response
- Browser demo, backend proxy, Dify workflow specification, and sample output

### Out of scope

- Real-time web search or cited market research
- Market sizing and forecasts
- Verified competitor intelligence
- Copy generation, channel plans, or complete growth strategy
- Authentication, persistence, collaboration, billing, and production analytics

## 6. User flow

1. User opens the demo and reviews the example brief.
2. User edits six fields and selects a business goal.
3. System validates the submission.
4. Context Interpreter normalizes the brief and exposes assumptions.
5. User Insight generates structured hypotheses.
6. UI displays insights, assumptions, confidence, and suggested research questions.

## 7. Functional requirements

| ID | Requirement | Acceptance criterion |
|---|---|---|
| FR-01 | Collect the six-field brief | Required fields reject blank values |
| FR-02 | Restrict business goal | Value matches one of six supported goals |
| FR-03 | Normalize context | Output contains summary, product category, growth stage, constraints, and assumptions |
| FR-04 | Generate user insight | All six insight sections contain useful content |
| FR-05 | Separate inference from fact | Response includes assumptions and no unsupported statistics |
| FR-06 | Enforce contract | Output validates against the repository JSON Schema and backend models |
| FR-07 | Fail safely | Dify timeout/configuration errors return a readable API error without leaking secrets |
| FR-08 | Demo without keys | Mock mode returns a complete deterministic example |

## 8. Non-functional requirements

- Blocking API response target: under 30 seconds in Dify mode
- Responsive interface at 360 px and above
- No Dify API key in frontend code or browser network requests
- Accessible labels, keyboard submission, visible focus, and sufficient contrast
- Prompts and output schemas versioned in Git

## 9. Success measures

Portfolio/product validation metrics for five moderated tests:

- 80% of users can explain the target-user hypothesis after one scan
- Median time to first usable research question below three minutes
- At least 70% of generated items rated “specific enough to test”
- 100% of successful calls pass schema validation
- Zero fabricated quantitative claims in the evaluation set

## 10. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Generic output | Context normalization, bounded audience, item-level “why it matters” |
| Hallucinated research | Hypothesis framing and explicit prohibition on invented evidence |
| Brittle JSON | Native structured output plus backend schema validation |
| Vendor coupling | Stable backend contract isolates the frontend from Dify |
| Portfolio feels like a mockup | Runnable mock, real API adapter, tests, sample artifact, architecture rationale |

## 11. Release definition

V0.1 is complete when the local frontend submits to the backend in mock mode, the same backend can invoke a published Dify Workflow via environment variables, and both paths return the documented schema.

