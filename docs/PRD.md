# Product Requirements Document — V0.3

## 1. Product definition

AI Growth Agent is an evidence-aware decision-support product for overseas growth operators. It converts a loosely written product brief into a traceable chain of user insight, market hypotheses, value propositions, and validation priorities.

V0.3 upgrades the product from answering only **who the user may be** to also answering **where the initial opportunity may exist** and **which value should be tested**. It remains a hypothesis product, not a market-research product.

## 2. Problem

Growth teams often jump from an incomplete product brief directly to channel or content ideas. Even when an LLM produces plausible recommendations, the operator may not know which user problem supports a market claim, whether a value proposition uses a real product capability, or what should be validated first.

V0.2.1 established a reliable, evidence-aware User Insight module. The next product gap is decision continuity: downstream market and messaging recommendations must be grounded in that upstream insight rather than generated as disconnected prose.

## 3. Target user

Primary user: a growth or product-operations professional responsible for an AI, SaaS, or consumer technology product entering or expanding in an overseas market.

Typical roles:

- Overseas Growth Operator
- Growth Manager
- Product Operations Manager
- International Marketing Manager
- Early-stage AI founder

## 4. Job to be done

When I receive an incomplete growth brief, help me identify a plausible user, an initial market wedge, and a value proposition worth testing so I can plan discovery and messaging validation without mistaking AI inference for verified research.

## 5. V0.3 product outcome

The product should connect three decisions:

1. **Who** — which user, job, friction, and scenario should be prioritized?
2. **Why now** — which behavior change, current alternative, or entry scenario may create an opportunity?
3. **Why us** — which functional, emotional, or social value should be tested against that opportunity?

## 6. Scope

### In scope

- Existing six-field growth brief and Context Interpreter
- Existing evidence-aware User Insight module
- Market Hypothesis: opportunity, current alternatives, behavior hypotheses, growth wedge, competitive frame, risks, and validation priorities
- Value Proposition: functional, emotional, and social value; positioning; reasons to believe; message pillars; objections; and message tests
- Item-level evidence, confidence, validation status, priority, and upstream `source_refs`
- Deterministic validation of cross-module references and consistency
- Strategy summary for the primary user, growth wedge, primary value, and biggest risk
- Versioned Dify prompts, schemas, workflow guide, backend contract, UI, tests, and evaluation artifacts

### Out of scope

- Real-time web search, citations, or market sizing
- Verified competitor intelligence or competitor performance claims
- Channel recommendations, content calendars, or generated ad copy
- Automated publishing, ad buying, CRM, or analytics integrations
- Authentication, persistence, collaboration, billing, or saved projects
- Multi-agent autonomy

## 7. User flow

1. User submits the existing six-field growth brief.
2. Context Interpreter normalizes facts, assumptions, and ambiguities.
3. User Insight generates evidence-aware user hypotheses.
4. Market Hypothesis identifies a narrow opportunity and validation priorities using upstream references.
5. Value Proposition converts the opportunity into testable value and message directions.
6. The server reframes risky claim language and validates structure, evidence, references, and cross-module consistency.
7. The UI presents a strategy summary, three modules, traceability, validation priorities, and quality status.

## 8. Functional requirements

| ID | Requirement | Acceptance criterion |
|---|---|---|
| FR-01 | Preserve the V0.2 request contract | The existing six input fields and six business goals remain valid |
| FR-02 | Preserve User Insight compatibility | `/api/v2/insights` and the V0.2.1 UI path continue to work |
| FR-03 | Generate a market hypothesis | Output includes every required V0.3 market section and passes its JSON Schema |
| FR-04 | Generate a value proposition | Output includes functional, emotional, and social value plus positioning and tests |
| FR-05 | Trace recommendations upstream | Every material market and value item contains at least one `source_ref` |
| FR-06 | Avoid fabricated research | Unsupported market, competitor, frequency, or willingness-to-pay claims are framed as hypotheses |
| FR-07 | Ground product claims | A reason to believe is `brief_supported` only when the capability exists in the normalized brief |
| FR-08 | Validate cross-module consistency | Target user, business goal, growth wedge, and primary value do not contradict upstream objects |
| FR-09 | Separate blockers from notes | Structural, evidence, or invalid-reference failures block; wording and research notes do not |
| FR-10 | Return a decision summary | Response exposes primary user, growth wedge, primary value, and biggest risk |
| FR-11 | Fail safely | Upstream or validation failures return readable errors without credentials or raw provider data |

## 9. Evidence and traceability contract

Every material generated item must include:

- `source_refs`: one or more paths into an upstream object
- `evidence.basis`: `explicit_brief`, `contextual_inference`, or `behavioral_hypothesis`
- `evidence.confidence`: `low`, `medium`, or `high`
- `evidence.validation_status`: `brief_supported` or `needs_validation`

Rules:

- `high` confidence is allowed only for `explicit_brief`.
- `brief_supported` is allowed only for `explicit_brief`.
- A source reference proves traceability to supplied context; it does not prove external truth.
- The server must confirm that each path resolves to an existing field.
- A downstream item cannot claim stronger evidence than its weakest valid upstream source.

## 10. Quality gate

V0.3 retains the three public states:

- `passed`: no unresolved issue remains after deterministic revision
- `passed_with_notes`: only non-blocking research or wording notes remain
- `review_required`: structure, evidence, product grounding, or source-reference validation failed

New deterministic checks:

- Market-claim language safety
- Validity of every `source_ref`
- Evidence consistency across modules
- Target-user and business-goal consistency
- Value-to-JTBD/pain linkage
- Reason-to-believe product grounding
- Required primary priorities and validation actions

## 11. Non-functional requirements

- Preserve a stable versioned product API; introduce `POST /api/v3/strategy`
- Keep the complete blocking workflow within a measured latency and token budget
- No provider key in frontend code, responses, logs, or Git history
- Responsive interface at 360 px and above
- Accessible navigation between strategy modules
- Prompts, schemas, evaluation cases, and product decisions versioned in Git

## 12. Success measures

Release-candidate gates on the fixed 12-case regression set:

- 12/12 workflow executions succeed
- 100% response-schema compliance
- 100% business-goal consistency
- 100% `source_refs` resolve to real upstream fields
- Zero unmarked factual market, competitor, or willingness-to-pay claims
- Every primary value links to at least one user job or pain
- Every case returns at least three actionable validation priorities
- V0.2.1 User Insight contract tests remain green

Human review continues to score specificity, relevance, internal consistency, testability, and unsupported-claim safety using the existing rubric. V0.3 must not claim user or business impact without real external evidence.

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Market output sounds like research | Name the module Market Hypothesis; prohibit unsupported factual language |
| Downstream modules drift from User Insight | Mandatory source references and cross-module validation |
| Product capabilities are invented | Separate reasons to believe and validate them against the normalized brief |
| Workflow becomes slow and expensive | Keep sequential nodes bounded; measure latency and tokens on the fixed set |
| UI becomes a long report | Lead with four decisions, then use module navigation and expandable traceability |
| V0.3 breaks the live V0.2 experience | Add a versioned API and retain V0.2.1 compatibility until regression passes |

## 14. Release definition

V0.3 is complete when the new Dify workflow produces all four structured objects, the server returns a validated strategy response through `/api/v3/strategy`, the public UI exposes traceable modules and quality status, and the fixed evaluation set meets every release-candidate gate.
