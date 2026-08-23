import { FormEvent, useState } from "react";
import { generateResearchStrategy } from "./api";
import type { BusinessGoal, GrowthBrief, InsightEvidence, InsightItem, ResearchStrategyResponse, StrategyResponse, TraceableItem } from "./types";

const goals: BusinessGoal[] = [
  "Brand Awareness",
  "User Acquisition",
  "Conversion",
  "Community Growth",
  "Product Launch",
  "Retention"
];

const initialBrief: GrowthBrief = {
  product: "AI Translation Earbuds",
  product_description: "Real-time AI translation earbuds designed for cross-language communication.",
  target_market: "United States",
  target_audience: "Frequent international business travelers",
  business_goal: "User Acquisition",
  additional_context: "The product is entering the US market. Competitors have a strong Amazon presence. We want to test Reddit and TikTok."
};

const evidenceLabels: Record<InsightEvidence["basis"], string> = {
  explicit_brief: "Brief evidence",
  contextual_inference: "Context inference",
  behavioral_hypothesis: "Behavioral hypothesis"
};

function EvidenceMeta({ evidence, relevance }: { evidence?: InsightEvidence; relevance?: "primary" | "secondary" }) {
  if (!evidence && !relevance) return null;
  return (
    <div className="insight-meta">
      {relevance && <span className={`relevance relevance-${relevance}`}>{relevance}</span>}
      {evidence && <span>{evidenceLabels[evidence.basis]}</span>}
      {evidence && <span>{evidence.confidence} confidence</span>}
      {evidence && <span>{evidence.validation_status === "brief_supported" ? "Brief supported" : "Needs validation"}</span>}
    </div>
  );
}

function SourceRefs({ item }: { item: TraceableItem }) {
  return (
    <details className="source-refs">
      <summary>{item.source_refs.length} source link{item.source_refs.length === 1 ? "" : "s"}</summary>
      <div>{item.source_refs.map((ref) => <code key={ref}>{ref}</code>)}</div>
    </details>
  );
}

function InsightList({ items }: { items: InsightItem[] }) {
  return (
    <ul className="insight-list">
      {items.map((item, index) => (
        <li key={`${item.insight}-${index}`}>
          <EvidenceMeta evidence={item.evidence} relevance={item.decision_relevance} />
          <p>{item.insight}</p>
          <small>{item.why_it_matters}</small>
        </li>
      ))}
    </ul>
  );
}

function QualityGate({ review }: { review: StrategyResponse["quality_review"] }) {
  const title = review.status === "review_required"
    ? "Human review required"
    : review.status === "passed_with_notes"
      ? "Passed with review notes"
      : "Strategy quality checks passed";
  const badge = review.status === "review_required"
    ? `${review.blocking_issue_count} blocker${review.blocking_issue_count === 1 ? "" : "s"}`
    : review.issue_count
      ? `${review.issue_count} review note${review.issue_count === 1 ? "" : "s"}`
      : "8 checks passed";

  return (
    <section className={`quality-gate quality-${review.status}`} aria-label="Deterministic quality gate">
      <div className="quality-heading">
        <div><span className="eyebrow">Deterministic quality gate</span><h3>{title}</h3></div>
        <span className="quality-status">{badge}</span>
      </div>
      {review.auto_revision_count > 0 && (
        <p className="quality-auto-note">
          {review.auto_revision_count} inferred claim{review.auto_revision_count === 1 ? " was" : "s were"} transparently reframed as {review.auto_revision_count === 1 ? "an explicit hypothesis" : "explicit hypotheses"} before review.
        </p>
      )}
      <div className="quality-checks quality-checks-v3">
        {review.checks.map((check) => (
          <div key={check.code} className={`quality-check check-${check.status}`}>
            <span aria-hidden="true">{check.status === "passed" ? "✓" : "!"}</span>
            <div><strong>{check.label}</strong><small>{check.detail}</small></div>
          </div>
        ))}
      </div>
      {review.issues.length > 0 && (
        <details className="quality-issues">
          <summary>See fields requiring review</summary>
          <ul>{review.issues.map((issue, index) => <li key={`${issue.path}-${index}`}><code>{issue.path}</code> — {issue.message}</li>)}</ul>
        </details>
      )}
    </section>
  );
}

function EvidenceBoard({ result }: { result: ResearchStrategyResponse }) {
  const coverage = result.evidence_brief.source_coverage;
  const sourceById = new Map(result.source_manifest.sources.map((source) => [source.source_id, source]));
  const statusLabel = result.research_status.replaceAll("_", " ");
  return (
    <section className="evidence-board" aria-label="Evidence Board">
      <div className="evidence-board-heading">
        <div><span className="eyebrow">Evidence Board · V0.5</span><h3>Research before recommendation.</h3></div>
        <span className={`research-status status-${result.research_status}`}>{statusLabel}</span>
      </div>
      <div className="coverage-strip">
        <div><strong>{coverage.answered_question_count}/{coverage.question_count}</strong><span>questions answered</span></div>
        <div><strong>{coverage.retained_source_count}</strong><span>sources retained</span></div>
        <div><strong>{result.evidence_brief.findings.filter((item) => item.status === "supported").length}</strong><span>supported findings</span></div>
        <div><strong>{result.evidence_audit.issue_count}</strong><span>gate corrections</span></div>
      </div>
      <p className="research-summary">{result.research_summary.evidence_coverage}</p>
      <div className="finding-list">
        {result.evidence_brief.findings.map((finding) => {
          const ids = [...finding.supporting_source_ids, ...finding.contradicting_source_ids];
          return (
            <article key={finding.finding_id} className={`evidence-finding finding-${finding.status}`}>
              <div className="finding-topline"><span>{finding.finding_id}</span><span>{finding.status}</span><span>{finding.confidence} confidence</span></div>
              <h4>{finding.claim}</h4><p>{finding.implication}</p>
              {ids.length > 0 && <div className="source-links">{ids.map((id) => { const source = sourceById.get(id); return source ? <a key={id} href={source.url} target="_blank" rel="noreferrer">{id} · {source.domain} ↗</a> : null; })}</div>}
              {finding.limitations.length > 0 && <small>Limits: {finding.limitations.join(" ")}</small>}
            </article>
          );
        })}
      </div>
      <details className="research-plan"><summary>View the five research questions</summary><ol>{result.research_plan.questions.map((question) => <li key={question.question_id}><strong>{question.question_id}</strong> {question.question}</li>)}</ol></details>
      <p className="research-gap"><strong>Largest gap:</strong> {result.research_summary.largest_research_gap}</p>
    </section>
  );
}

function Results({ result }: { result: ResearchStrategyResponse }) {
  const { strategy_summary: summary, user_insight: insight, market_hypothesis: market, value_proposition: value } = result;
  return (
    <section className="results strategy-results" aria-live="polite">
      <div className="results-header">
        <div>
          <span className="eyebrow">Evidence-backed strategy · V0.5</span>
          <h2>{summary.primary_user}</h2>
          <p>{result.context.brief_summary}</p>
        </div>
        <span className={`confidence confidence-${market.confidence}`}>{market.confidence} confidence</span>
      </div>

      <div className="strategy-summary" aria-label="Strategy decision summary">
        <article><span>Primary user</span><p>{summary.primary_user}</p></article>
        <article><span>Growth wedge</span><p>{summary.growth_wedge}</p></article>
        <article><span>Primary value</span><p>{summary.primary_value}</p></article>
        <article className="risk-summary"><span>Biggest risk</span><p>{summary.biggest_risk}</p></article>
      </div>

      <EvidenceBoard result={result} />

      <QualityGate review={result.research_quality_review} />

      <details className="context" open>
        <summary>01 · Context Interpreter</summary>
        <p>{result.context.brief_summary}</p>
        <div className="context-columns">
          <div><strong>Assumptions</strong><ul>{result.context.assumptions.map((item) => <li key={item}>{item}</li>)}</ul></div>
          <div><strong>Ambiguities</strong><ul>{result.context.ambiguities.map((item) => <li key={item}>{item}</li>)}</ul></div>
        </div>
      </details>

      <div className="module-heading"><span>02</span><div><h3>User Insight</h3><p>Who matters, what they are trying to do, and what still needs validation.</p></div></div>
      <div className="result-grid">
        <article className="wide-card">
          <h3>Jobs to be done</h3>
          <ul className="jobs">
            {insight.jobs_to_be_done.map((item, index) => (
              <li key={index}>
                <div className="job-labels"><span>{item.dimension}</span><EvidenceMeta evidence={item.evidence} relevance={item.decision_relevance} /></div>
                <p>{item.job}</p><small>{item.why_it_matters}</small>
              </li>
            ))}
          </ul>
        </article>
        <article><h3>Pain points</h3><InsightList items={insight.pain_points} /></article>
        <article><h3>Adoption barriers</h3><InsightList items={insight.adoption_barriers} /></article>
        <article className="wide-card research-card"><h3>Research questions</h3><ol>{insight.research_questions.map((question) => <li key={question}>{question}</li>)}</ol></article>
      </div>

      <div className="module-heading"><span>03</span><div><h3>Market Hypothesis</h3><p>A traceable opportunity frame—not a substitute for market research.</p></div></div>
      <div className="market-grid">
        <article className="opportunity-card">
          <span className="micro-label">Opportunity hypothesis</span>
          <h3>{market.opportunity_statement.hypothesis}</h3>
          <p>{market.opportunity_statement.why_now}</p>
          <EvidenceMeta evidence={market.opportunity_statement.evidence} />
          <SourceRefs item={market.opportunity_statement} />
        </article>
        <article className="wedge-card">
          <span className="micro-label">Growth wedge</span>
          <h3>{market.growth_wedge.entry_scenario}</h3>
          <p>{market.growth_wedge.rationale}</p>
          <SourceRefs item={market.growth_wedge} />
        </article>
        <article className="wide-market-card">
          <div className="card-heading"><h3>What to validate first</h3><span>{market.validation_priorities.length} tests</span></div>
          <div className="validation-list">
            {market.validation_priorities.map((item, index) => (
              <div key={item.hypothesis_to_test}>
                <span className={`priority priority-${item.priority}`}>{index + 1} · {item.priority}</span>
                <h4>{item.hypothesis_to_test}</h4>
                <p>{item.method}</p>
                <dl><div><dt>Pass</dt><dd>{item.pass_signal}</dd></div><div><dt>Fail</dt><dd>{item.fail_signal}</dd></div></dl>
                <SourceRefs item={item} />
              </div>
            ))}
          </div>
        </article>
        <article className="wide-market-card risk-card">
          <div className="card-heading"><h3>Main risks</h3><span>Human decision required</span></div>
          <ul className="risk-list">{market.main_risks.map((item) => <li key={item.risk}><span className={`priority priority-${item.priority}`}>{item.priority}</span><div><strong>{item.risk}</strong><small>{item.consequence}</small></div></li>)}</ul>
        </article>
      </div>

      <div className="module-heading"><span>04</span><div><h3>Value Proposition</h3><p>Turns the upstream evidence into a positioning and message-testing plan.</p></div></div>
      <article className="positioning-card">
        <span className="micro-label">Positioning statement</span>
        <blockquote>{value.positioning_statement}</blockquote>
        <div className="primary-value"><strong>Primary value</strong><p>{value.primary_value.statement}</p><small>{value.primary_value.rationale}</small><SourceRefs item={value.primary_value} /></div>
      </article>
      <div className="message-grid">
        {value.message_pillars.map((pillar) => (
          <article key={pillar.name} className={pillar.priority === "primary" ? "primary-message" : ""}>
            <span className="micro-label">{pillar.priority} message</span><h3>{pillar.name}</h3><p>{pillar.message}</p><small>{pillar.user_problem}</small><SourceRefs item={pillar} />
          </article>
        ))}
      </div>
      <article className="test-plan-card">
        <h3>Message experiments</h3>
        {value.message_tests.map((test) => <div key={test.angle}><span>{test.angle.replaceAll("_", " ")}</span><p><strong>A</strong> {test.variant_a}</p><p><strong>B</strong> {test.variant_b}</p><small>Measure: {test.primary_metric} · Learn: {test.expected_learning}</small></div>)}
      </article>

      <p className="run-meta">Run {result.request_id.slice(0, 8)} · {result.mode} mode · researched {new Date(result.researched_at).toLocaleDateString()}</p>
    </section>
  );
}

function V05Overview() {
  const releases = [
    {
      number: "01",
      title: "Bounded research plan",
      copy: "The agent turns the brief into three to five decision-focused questions before it searches.",
      tag: "Plan before search",
    },
    {
      number: "02",
      title: "Current source retrieval",
      copy: "Live search results are normalized, deduplicated, and capped at ten retained sources.",
      tag: "Source manifest",
    },
    {
      number: "03",
      title: "Deterministic Evidence Gate",
      copy: "Question mismatch, weak provenance, and unsupported confidence are corrected before strategy generation.",
      tag: "Trust by contract",
    },
    {
      number: "04",
      title: "Claim-level citation map",
      copy: "Material recommendations resolve to retained findings—or stay visibly labeled as inference or unknown.",
      tag: "Audit every claim",
    },
  ];

  return (
    <section className="release-overview" id="whats-new" aria-labelledby="release-title">
      <div className="release-intro">
        <div>
          <span className="release-kicker"><i /> Now live · V0.5</span>
          <h2 id="release-title">The strategy now begins with evidence.</h2>
        </div>
        <p>V0.5 upgrades AI Growth Agent from a traceable strategy generator into a bounded research workflow. It plans what to investigate, retrieves current sources, audits evidence quality, and preserves citation continuity all the way to the final recommendation.</p>
      </div>

      <div className="release-grid">
        {releases.map((item) => (
          <article key={item.number} className="release-card">
            <div className="release-card-top"><span>{item.number}</span><em>{item.tag}</em></div>
            <h3>{item.title}</h3>
            <p>{item.copy}</p>
          </article>
        ))}
      </div>

      <div className="release-flow" aria-label="V0.5 workflow">
        {[
          ["Brief", "Human context"],
          ["Plan", "3–5 questions"],
          ["Search", "Live sources"],
          ["Gate", "Evidence audit"],
          ["Synthesize", "Findings"],
          ["Strategy", "Decision chain"],
          ["Cite", "Claim map"],
        ].map(([title, copy], index) => (
          <div className="release-flow-item" key={title}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <strong>{title}</strong>
            <small>{copy}</small>
          </div>
        ))}
      </div>

      <div className="release-proof">
        <div><strong>22/22</strong><span>workflow nodes succeeded</span></div>
        <div><strong>3/3</strong><span>GitHub CI jobs passed</span></div>
        <div><strong>8</strong><span>research-quality checks</span></div>
        <div><strong>9</strong><span>typed workflow outputs</span></div>
      </div>
    </section>
  );
}

function CaseStudy() {
  return (
    <section className="case-study" id="case-study" aria-labelledby="case-study-title">
      <div className="case-study-intro">
        <div><span className="eyebrow">Product case study</span><h2 id="case-study-title">A growth brief becomes a decision-ready strategy chain.</h2></div>
        <p>V0.5 demonstrates the full research-to-decision loop: bounded search, source provenance, deterministic evidence controls, typed strategy contracts, claim citations, regression tests, and a deployable interface.</p>
      </div>

      <div className="case-study-grid">
        <article className="case-card problem-card"><span className="card-index">01 · Problem</span><h3>Growth teams receive fragmented context.</h3><p>Generic tools jump to campaigns before clarifying the user, evidence, constraints, and unknowns.</p></article>
        <article className="case-card"><span className="card-index">02 · Target user</span><h3>Overseas growth operators for AI and technology products.</h3><p>Built for growth managers, product operators, international marketers, and early-stage founders.</p></article>
        <article className="case-card decision-card"><span className="card-index">03 · Product decision</span><h3>Trace decisions, not just text.</h3><p>Every downstream recommendation points back to context, user evidence, or a market hypothesis.</p></article>
      </div>

      <div className="case-section workflow-section">
        <div className="section-heading"><span className="card-index">04 · How it works</span><h3>Research, evidence, strategy, and citation in one controlled workflow.</h3></div>
        <div className="workflow-steps workflow-v3" aria-label="AI Growth Agent workflow">
          {[
            ["01", "Growth brief", "Six fields capture product, market, audience, goal, and constraints."],
            ["02", "Research plan", "Creates three to five bounded questions tied to a real decision."],
            ["03", "Live retrieval", "Searches current sources and preserves query provenance."],
            ["04", "Evidence Gate", "Rejects mismatches and caps unsupported confidence."],
            ["05", "Strategy chain", "Builds user insight, market hypothesis, and value proposition."],
            ["06", "Citation map", "Resolves material claims to retained findings and sources."]
          ].map(([number, title, copy], index) => (
            <div className="workflow-fragment" key={number}><div className="workflow-step"><strong>{number}</strong><div><h4>{title}</h4><p>{copy}</p></div></div>{index < 5 && <span className="workflow-arrow" aria-hidden="true">→</span>}</div>
          ))}
        </div>
      </div>

      <div className="case-split">
        <article className="responsible-card"><span className="card-index">05 · Responsible AI</span><h3>Hypotheses, not fabricated authority.</h3><ul><li>No invented statistics, quotes, citations, or competitor facts</li><li>Evidence strength cannot exceed its weakest source</li><li>Risky inferred claims are visibly reframed before review</li><li>Measurable pass and fail signals keep validation actionable</li><li>The human owns prioritization and commercial decisions</li></ul></article>
        <article className="architecture-card"><span className="card-index">06 · Architecture</span><h3>A secure, streaming product boundary.</h3><div className="architecture-flow architecture-v3"><span>React UI</span><i>→</i><span>Edge stream</span><i>→</i><span>Dify V0.5</span><i>→</i><span>Evidence Board</span></div><p>The browser consumes a same-origin event stream. Credentials stay server-side while the final typed output preserves sources, audits, findings, strategy, and citations.</p></article>
      </div>

      <div className="evaluation-section">
        <div className="section-heading"><span className="card-index">07 · Evaluation</span><h3>Quality is treated as product behavior.</h3></div>
        <div className="evidence-grid"><div><strong>56</strong><span>automated regression tests</span></div><div><strong>8</strong><span>research-quality checks</span></div><div><strong>9</strong><span>typed workflow outputs</span></div><div><strong>0</strong><span>client-side API secrets</span></div></div>
        <div className="evaluation-findings">
          <article><span className="finding-label">Baseline</span><h4>V0.1 exposed fluent but overconfident claims.</h4><p>A fixed 12-case evaluation showed relevance was stronger than unsupported-claim safety.</p></article>
          <article className="finding-risk"><span className="finding-label">Iteration</span><h4>V0.2 added item-level evidence and review status.</h4><p>Evidence basis, confidence, decision relevance, and behavior-first questions became part of the output contract.</p></article>
          <article className="finding-decision"><span className="finding-label">V0.5 decision</span><h4>Research before recommendation.</h4><p>Current sources now pass through an Evidence Gate before strategy claims receive citations, confidence, or action priority.</p></article>
        </div>
        <p className="evaluation-note">Internal product evaluation—not a claim of user or business impact. <a href="https://github.com/ftw10181-oss/ai-growth-agent/tree/main/evals" target="_blank" rel="noreferrer">Review the evaluation artifacts <span aria-hidden="true">↗</span></a></p>
      </div>

      <div className="builder-card"><div><span className="eyebrow">Built by Markus</span><h3>Product strategy, workflow design, prompts, contracts, evaluation, frontend, and launch.</h3><p>This independent project demonstrates the full AI product loop: define a real growth problem, design the human–AI boundary, ship a working system, and make quality observable.</p></div><a href="https://github.com/ftw10181-oss/ai-growth-agent" target="_blank" rel="noreferrer">View GitHub <span aria-hidden="true">↗</span></a></div>
    </section>
  );
}

export default function App() {
  const [brief, setBrief] = useState<GrowthBrief>(initialBrief);
  const [result, setResult] = useState<ResearchStrategyResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const update = (key: keyof GrowthBrief, value: string) => setBrief((current) => ({ ...current, [key]: value }));

  async function handleSubmit(event: FormEvent) {
    event.preventDefault(); setError(""); setLoading(true);
    try { setResult(await generateResearchStrategy(brief)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Something went wrong."); }
    finally { setLoading(false); }
  }

  return (
    <main>
      <header className="hero">
        <nav><span className="brand-mark">AG</span><strong>AI Growth Agent</strong><div className="nav-links"><a href="#whats-new">What’s new</a><a href="#demo">Live workflow</a><a href="#case-study">Case study</a><a href="https://github.com/ftw10181-oss/ai-growth-agent" target="_blank" rel="noreferrer">GitHub ↗</a></div><span className="version">V0.5 · Live</span></nav>
        <div className="hero-copy"><span className="eyebrow">Evidence-backed growth intelligence · V0.5</span><h1>Research first.<br />Recommend second.</h1><p>Turn a fuzzy product brief into current findings, a source-aware Evidence Board, and a traceable growth strategy—with every uncertainty left visible for human judgment.</p><div className="hero-actions"><a className="primary-action" href="#demo">Run the V0.5 workflow <span aria-hidden="true">↓</span></a><a className="secondary-action" href="#whats-new">Explore the release</a></div><div className="hero-proof"><span><strong>Live research</strong>Current web sources</span><span><strong>Evidence Gate</strong>Deterministic controls</span><span><strong>Citation map</strong>Claim-level traceability</span><span><strong>Production verified</strong>22-node workflow</span></div></div>
      </header>

      <V05Overview />

      <section className="workspace" id="demo">
        <form onSubmit={handleSubmit}>
          <div className="form-heading"><div><span className="step">01</span><h2>Growth brief</h2></div><p>Six fields. About two minutes.</p></div>
          <div className="field-row"><label>Product<input value={brief.product} onChange={(event) => update("product", event.target.value)} minLength={2} maxLength={120} required /></label><label>Target market<input value={brief.target_market} onChange={(event) => update("target_market", event.target.value)} minLength={2} maxLength={120} required /></label></div>
          <label>Product description<textarea value={brief.product_description} onChange={(event) => update("product_description", event.target.value)} minLength={20} maxLength={2000} rows={3} required /></label>
          <div className="field-row"><label>Target audience<input value={brief.target_audience} onChange={(event) => update("target_audience", event.target.value)} minLength={5} maxLength={500} required /></label><label>Business goal<select value={brief.business_goal} onChange={(event) => update("business_goal", event.target.value)}>{goals.map((goal) => <option key={goal}>{goal}</option>)}</select></label></div>
          <label>Additional context <span className="optional">optional</span><textarea value={brief.additional_context} onChange={(event) => update("additional_context", event.target.value)} maxLength={2000} rows={3} /></label>
          <div className="submit-row"><p>V0.5 searches up to five questions, validates evidence, then builds the strategy.</p><button disabled={loading}>{loading ? "Researching evidence…" : "Research & build strategy"}<span aria-hidden="true">→</span></button></div>
          {error && <p className="error" role="alert">{error}</p>}
        </form>
        {result ? <Results result={result} /> : <aside className={`empty-state ${loading ? "loading-state" : ""}`}><span className="step">02</span><h2>{loading ? "Research workflow in progress." : "Your Evidence Board will appear here."}</h2><p>{loading ? "The live workflow is planning questions, retrieving sources, and auditing evidence. A full V0.5 run can take around two minutes." : "The agent plans research, retrieves current sources, audits evidence strength, and only then creates a traceable strategy."}</p><div className="pipeline"><span>Plan</span><i>→</i><span>Search</span><i>→</i><span>Gate</span><i>→</i><span>Strategy</span></div>{loading && <div className="loading-progress"><i /><span>Keep this tab open while the evidence stream completes.</span></div>}</aside>}
      </section>
      <CaseStudy />
      <footer><span>Built by Markus for overseas growth operators</span><span>Traceable · transparent · testable</span></footer>
    </main>
  );
}
