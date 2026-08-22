# Product Requirements Document — V0.5

Status: design baseline  
Release theme: evidence-backed growth research

## 1. Product definition

AI Growth Agent V0.5 turns a six-field growth brief into a research-backed,
traceable growth strategy. It plans a bounded web investigation, records the
sources it actually retrieved, separates external evidence from inference, and
links every material strategy claim to evidence or marks it for validation.

V0.5 changes the product category from an inference-only strategy assistant to
an evidence-aware research and decision-support product.

## 2. User problem

V0.3 can create a coherent chain from user hypothesis to market hypothesis and
value proposition, but it cannot establish whether the market context is
current or externally supported. A plausible answer may still be based only on
the submitted brief and model priors.

Growth operators need a faster way to answer:

1. Which questions require external evidence before a strategy decision?
2. Which current sources support, contradict, or fail to answer those questions?
3. Which claims are evidence-backed, which remain inference, and what should be
   validated next?

## 3. Target user and job to be done

Primary user: an overseas growth, product-operations, or early-stage product
lead evaluating an AI, SaaS, or consumer-technology product in a new market.

Job to be done:

> When I receive an incomplete market-entry or growth brief, help me collect
> relevant current evidence and turn it into a traceable strategy so I can make
> a better research or validation decision without mistaking search snippets or
> AI inference for verified fact.

## 4. Product principles

1. **Research before recommendation.** The workflow must define the questions
   and evidence threshold before it searches.
2. **Retrieved is not verified.** A search result proves retrieval, not truth.
3. **Citations must be inspectable.** A claim may cite only a source that exists
   in the returned source manifest.
4. **Conflicts remain visible.** Contradictory findings cannot be silently
   averaged into a confident conclusion.
5. **Uncertainty is a product output.** Missing evidence and search failure must
   be shown, not hidden by fluent prose.
6. **Search is bounded.** V0.5 optimizes for decision value, latency, and cost,
   not exhaustive research.

## 5. V0.5 outcome

The product should answer five connected questions:

1. **Research scope** — what must be investigated for this decision?
2. **Evidence** — what current sources were retrieved and how useful are they?
3. **User** — which user and problem remain most plausible after research?
4. **Opportunity** — which market wedge is supported, contested, or still open?
5. **Value** — which proposition should be tested and why?

## 6. Scope

### In scope

- Existing six-field growth brief and V0.3 strategy modules
- Research Planner with three to five decision-focused questions
- Web Search through a Dify Tool node
- Deterministic source normalization, URL deduplication, and source IDs
- Evidence Synthesizer with supported, contested, and insufficient findings
- Source title, URL, domain, publisher, publication date when available,
  retrieval date, source class, and search-query traceability
- Claim-to-evidence citation map for material strategy claims
- Separate labels for evidence, inference, assumption, and unknown
- Citation, coverage, conflict, freshness, and wording quality checks
- Search-failure fallback to the V0.3 inference-only strategy
- Versioned API, schemas, prompts, workflow guide, tests, and UI states

### Out of scope

- Exhaustive academic, legal, medical, or investment research
- Scraping pages that block access or require authentication
- Automated market sizing or financial forecasting
- Autonomous multi-hop browsing without query and cost limits
- Treating vendor marketing copy, snippets, or model-generated summaries as
  independent validation
- Automated campaign publishing, ad buying, CRM writes, or customer outreach
- Continuous monitoring and scheduled research refreshes

## 7. User flow

1. User submits the existing growth brief.
2. Context Interpreter separates supplied facts, assumptions, and ambiguity.
3. Research Planner returns three to five questions, queries, and proof needs.
4. Search runs a bounded set of queries.
5. Source Normalizer removes duplicate URLs and creates immutable source IDs.
6. Source Evaluator records relevance, source class, freshness, and limitations.
7. Evidence Synthesizer groups findings as supported, contested, or insufficient.
8. A deterministic evidence gate removes invalid or weak source links, enforces
   confidence ceilings, and recalculates question coverage.
9. User Insight, Market Hypothesis, and Value Proposition consume the validated
   evidence brief and retain V0.3 upstream traceability.
10. The product API performs final citation, continuity, and claim-language checks.
11. The UI shows the strategy, evidence board, sources, gaps, and review state.

## 8. Functional requirements

| ID | Requirement | Acceptance criterion |
|---|---|---|
| FR-01 | Preserve the V0.3 brief | Existing six fields and business goals remain valid |
| FR-02 | Plan research before search | Three to five questions each define a query, evidence need, and decision impact |
| FR-03 | Bound external search | Maximum five queries and ten retained sources per run |
| FR-04 | Preserve raw provenance | Every retained source has an immutable ID, canonical URL, query ID, and retrieval timestamp; the global source cap is allocated across research questions rather than consumed by the first query |
| FR-05 | Evaluate source usefulness | Every source exposes relevance, source class, freshness, and limitations |
| FR-06 | Synthesize evidence | Findings expose supported, contested, or insufficient status and source IDs |
| FR-07 | Prevent citation invention | Every citation resolves to a retained source and every source URL came from tool output |
| FR-08 | Connect evidence to strategy | Every material market claim is linked through a claim citation or marked `needs_validation` |
| FR-09 | Preserve conflict | A contested finding lists supporting and contradicting source IDs |
| FR-10 | Fail transparently | Search failure returns V0.3 strategy plus `research_status=unavailable` |
| FR-11 | Protect secrets and quota | Search credentials remain server-side and requests are rate/cost limited |
| FR-12 | Expose decision summary | Response adds evidence coverage and largest research gap to the V0.3 summary |
| FR-13 | Enforce evidence before strategy | A deterministic workflow gate rejects mismatched or low-relevance source links and caps unsupported confidence before strategy generation |

## 9. Evidence contract

### Source record

A source record contains retrieval metadata. It does not certify truth.

- `source_id`
- `title`
- `url`
- `domain`
- `publisher`
- `published_at` when available
- `retrieved_at`
- `query_ids`
- `source_class`: `primary`, `independent_secondary`, `vendor`, `community`, or
  `unknown`
- `relevance_score`: zero to one
- `freshness`: `current`, `dated`, or `unknown`
- `limitations`

### Evidence finding

An evidence finding contains:

- `finding_id`
- `claim`
- `dimension`: user behavior, market context, competitor, channel, risk, or
  product expectation
- `status`: supported, contested, or insufficient
- `supporting_source_ids`
- `contradicting_source_ids`
- `confidence`: low, medium, or high
- `implication`
- `limitations`

`high` confidence requires at least two relevant sources, including one primary
or independent-secondary source. Vendor and community sources may provide
signals but cannot independently justify `high` confidence.

### Claim citation

A strategy claim citation contains:

- exact `claim_path` into the public strategy response
- one or more `finding_ids`
- `claim_status`: evidence-backed, contested, inference, or unknown
- a short explanation of why the evidence applies

## 10. Quality gate

V0.5 extends the public quality states:

- `passed`: structure and evidence contracts pass; no blocking conflict remains
- `passed_with_notes`: non-blocking freshness, source diversity, or evidence-gap
  notes remain
- `review_required`: invented citation, invalid URL provenance, hidden conflict,
  unsupported factual language, or missing critical evidence is present

Checks:

1. Research-plan contract
2. Source-manifest integrity
3. Citation resolution
4. Evidence coverage
5. Conflict preservation
6. Source diversity and freshness
7. Claim-language consistency
8. V0.3 strategy continuity and product grounding

## 11. Non-functional requirements

- Introduce `POST /api/v5/research-strategy`; retain all V0.3 routes
- Store no search credential, Dify key, or raw provider authorization data in
  frontend code, responses, logs, or Git
- Enforce time, query, result, and daily usage limits
- Return partial research rather than discard usable sources after one query fails
- Cache identical research briefs for a bounded period
- Make citations keyboard accessible and open sources in a new tab
- Keep the interface usable at 360 px and above
- Include the research timestamp and research mode in every result

## 12. Release-candidate gates

On a fixed evaluation set of at least 12 briefs:

- 100% response-schema compliance
- 100% citations resolve to returned findings and sources
- 100% returned source URLs originate from the search-tool output
- Zero unsupported high-confidence findings
- Zero hidden contested findings
- Every case returns three to five research questions
- Every successful research run retains at least four relevant sources or
  explicitly reports insufficient coverage
- Every material market claim is evidence-backed, contested, inference, or unknown
- All V0.3 regression tests remain green

Human review scores decision relevance, source usefulness, evidence/claim fit,
specificity, conflict handling, and whether the output improves the next growth
decision. V0.5 must not claim business impact until measured with real users.

## 13. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Search snippets are mistaken for facts | Label retrieval separately; require finding synthesis and citation checks |
| The model fabricates or edits URLs | Build source IDs from tool output and reject unknown URLs |
| Results overrepresent vendor content | Expose source class and require diversity notes |
| Early queries consume the source budget | Retain results in rank-by-query order and test question-level coverage |
| Freshness is unknown | Preserve missing dates and lower confidence rather than invent them |
| Search adds latency and cost | Limit queries/results, cache briefs, and show partial progress |
| Evidence conflicts | Preserve both sides and trigger review for critical claims |
| Provider outage | Return V0.3 inference-only output with explicit unavailable status |
| Large output overwhelms recruiters | Lead with decisions and evidence coverage; keep sources expandable |

## 14. Release definition

V0.5 is complete when the Dify workflow performs bounded live search, the
server proves URL and citation integrity, the public UI exposes evidence and
uncertainty, the fixed evaluation set passes every release gate, and the V0.3
experience remains available as a safe fallback.
