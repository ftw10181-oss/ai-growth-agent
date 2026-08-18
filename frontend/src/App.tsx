import { FormEvent, useState } from "react";
import { generateInsight } from "./api";
import type { BusinessGoal, GrowthBrief, InsightEvidence, InsightItem, InsightResponse } from "./types";

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

function InsightMeta({ evidence, relevance }: { evidence?: InsightEvidence; relevance?: "primary" | "secondary" }) {
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

function InsightList({ items }: { items: InsightItem[] }) {
  return (
    <ul className="insight-list">
      {items.map((item, index) => (
        <li key={`${item.insight}-${index}`}>
          <InsightMeta evidence={item.evidence} relevance={item.decision_relevance} />
          <p>{item.insight}</p>
          <small>{item.why_it_matters}</small>
        </li>
      ))}
    </ul>
  );
}

function Results({ result }: { result: InsightResponse }) {
  const insight = result.user_insight;
  const review = result.quality_review;
  const qualityTitle = review?.status === "review_required"
    ? "Human review required"
    : review?.status === "passed_with_notes"
      ? "Passed with review notes"
      : "Quality checks passed";
  const qualityBadge = review?.status === "review_required"
    ? `${review.issue_count} blocking flag${review.issue_count === 1 ? "" : "s"}`
    : review?.status === "passed_with_notes"
      ? `${review.issue_count} review note${review.issue_count === 1 ? "" : "s"}`
      : review?.auto_revision_count
        ? `${review.auto_revision_count} phrase${review.auto_revision_count === 1 ? "" : "s"} reframed`
        : "4 checks passed";
  return (
    <section className="results" aria-live="polite">
      <div className="results-header">
        <div>
          <span className="eyebrow">User Insight · V0.2.1</span>
          <h2>{insight.target_user.primary_segment}</h2>
          <p>{insight.target_user.rationale}</p>
        </div>
        <span className={`confidence confidence-${insight.confidence}`}>{insight.confidence} confidence</span>
      </div>

      {review && (
        <section className={`quality-gate quality-${review.status}`} aria-label="Deterministic quality gate">
          <div className="quality-heading">
            <div>
              <span className="eyebrow">Deterministic quality gate</span>
              <h3>{qualityTitle}</h3>
            </div>
            <span className="quality-status">{qualityBadge}</span>
          </div>
          {review.auto_revision_count > 0 && (
            <p className="quality-auto-note">
              The service transparently reframed {review.auto_revision_count} high-risk phrase{review.auto_revision_count === 1 ? "" : "s"} as explicit hypotheses before this review.
            </p>
          )}
          <div className="quality-checks">
            {review.checks.map((check) => (
              <div key={check.code} className={`quality-check check-${check.status}`}>
                <span aria-hidden="true">{check.status === "passed" ? "✓" : "!"}</span>
                <div><strong>{check.label}</strong><small>{check.detail}</small></div>
              </div>
            ))}
          </div>
          {review.issues.length > 0 && (
            <details className="quality-issues">
              <summary>{review.status === "review_required" ? "See blocking fields" : "See review notes"}</summary>
              <ul>{review.issues.map((issue, index) => <li key={`${issue.path}-${index}`}><code>{issue.path}</code> — {issue.message}</li>)}</ul>
            </details>
          )}
        </section>
      )}

      <details className="context" open>
        <summary>How the brief was interpreted</summary>
        <p>{result.context.brief_summary}</p>
      </details>

      <div className="result-grid">
        <article className="wide-card">
          <h3>Jobs to be done</h3>
          <ul className="jobs">
            {insight.jobs_to_be_done.map((item, index) => (
              <li key={index}>
                <div className="job-labels">
                  <span>{item.dimension}</span>
                  <InsightMeta evidence={item.evidence} relevance={item.decision_relevance} />
                </div>
                <p>{item.job}</p>
                <small>{item.why_it_matters}</small>
              </li>
            ))}
          </ul>
        </article>
        <article><h3>Pain points</h3><InsightList items={insight.pain_points} /></article>
        <article><h3>Purchase motivations</h3><InsightList items={insight.purchase_motivations} /></article>
        <article><h3>Adoption barriers</h3><InsightList items={insight.adoption_barriers} /></article>
        <article><h3>Typical scenarios</h3><InsightList items={insight.typical_scenarios} /></article>
        <article className="wide-card research-card">
          <h3>Questions to take into research</h3>
          <ol>{insight.research_questions.map((question, index) => <li key={index}>{question}</li>)}</ol>
        </article>
      </div>

      <div className="assumptions">
        <h3>Assumptions to validate</h3>
        <ul>{insight.assumptions_to_validate.map((item, index) => <li key={index}>{item}</li>)}</ul>
      </div>
      <p className="run-meta">Run {result.request_id.slice(0, 8)} · {result.mode} mode · hypotheses, not verified research</p>
    </section>
  );
}

function CaseStudy() {
  return (
    <section className="case-study" id="case-study" aria-labelledby="case-study-title">
      <div className="case-study-intro">
        <div>
          <span className="eyebrow">Product case study</span>
          <h2 id="case-study-title">Why this product exists—and how it was built.</h2>
        </div>
        <p>
          AI Growth Agent is a portfolio-grade vertical slice: a real workflow, a stable product
          contract, and a public interface designed around one upstream growth problem.
        </p>
      </div>

      <div className="case-study-grid">
        <article className="case-card problem-card">
          <span className="card-index">01 · Problem</span>
          <h3>Growth work starts with fragmented context.</h3>
          <p>
            Product notes, audience assumptions, and stakeholder requests arrive unevenly. Generic
            AI tools often skip interpretation and jump straight to polished—but weak—campaign ideas.
          </p>
        </article>
        <article className="case-card">
          <span className="card-index">02 · Target user</span>
          <h3>Overseas growth operators for AI and technology products.</h3>
          <p>
            Built for growth managers, product operators, international marketers, and early-stage
            founders who need a better starting point for discovery and experimentation.
          </p>
        </article>
        <article className="case-card decision-card">
          <span className="card-index">03 · Product decision</span>
          <h3>Interpret first. Generate second.</h3>
          <p>
            The system makes facts, assumptions, constraints, and ambiguities visible before it
            produces user hypotheses. That creates a reusable context layer and reduces false confidence.
          </p>
        </article>
      </div>

      <div className="case-section workflow-section">
        <div className="section-heading">
          <span className="card-index">04 · How it works</span>
          <h3>A two-stage AI workflow with a deterministic safety layer.</h3>
        </div>
        <div className="workflow-steps" aria-label="AI Growth Agent workflow">
          <div className="workflow-step">
            <strong>01</strong>
            <div><h4>Growth brief</h4><p>Six fields capture the product, market, audience, goal, and constraints.</p></div>
          </div>
          <span className="workflow-arrow" aria-hidden="true">→</span>
          <div className="workflow-step">
            <strong>02</strong>
            <div><h4>Context Interpreter</h4><p>Normalizes the brief and exposes assumptions without inventing research.</p></div>
          </div>
          <span className="workflow-arrow" aria-hidden="true">→</span>
          <div className="workflow-step">
            <strong>03</strong>
            <div><h4>User Insight</h4><p>Returns testable jobs, pains, motivations, barriers, scenarios, and questions.</p></div>
          </div>
          <span className="workflow-arrow" aria-hidden="true">→</span>
          <div className="workflow-step">
            <strong>04</strong>
            <div><h4>Quality Gate</h4><p>Reframes risky claims as hypotheses, then separates blockers from review notes.</p></div>
          </div>
        </div>
      </div>

      <div className="case-split">
        <article className="responsible-card">
          <span className="card-index">05 · Responsible AI</span>
          <h3>Hypotheses, not fabricated authority.</h3>
          <ul>
            <li>No invented statistics, quotes, competitor claims, or citations</li>
            <li>Assumptions and ambiguities remain visible</li>
            <li>Confidence and research questions encourage human validation</li>
            <li>High-risk claim wording is transparently reframed—not hidden</li>
            <li>The human owns prioritization and commercial decisions</li>
          </ul>
        </article>

        <article className="architecture-card">
          <span className="card-index">06 · Architecture</span>
          <h3>A stable server-side boundary keeps the workflow secure.</h3>
          <div className="architecture-flow" aria-label="System architecture">
            <span>React UI</span><i>→</i><span>Server API</span><i>→</i><span>Dify</span>
          </div>
          <p>
            The browser calls a same-origin API. Dify credentials stay in encrypted server-side
            environment variables and never enter frontend code or Git history.
          </p>
        </article>
      </div>

      <div className="evaluation-section">
        <div className="section-heading">
          <span className="card-index">07 · Evaluation</span>
          <h3>A real baseline—including the failures.</h3>
        </div>
        <div className="evidence-grid">
          <div><strong>12/12</strong><span>live Dify runs succeeded</span></div>
          <div><strong>100%</strong><span>contract and goal consistency</span></div>
          <div><strong>3.75</strong><span>single-reviewer score · out of 5</span></div>
          <div><strong>2/12</strong><span>met the full publish threshold</span></div>
        </div>
        <div className="evaluation-findings">
          <article>
            <span className="finding-label">What held</span>
            <h4>Reliable execution, strong brief relevance.</h4>
            <p>
              All cases passed the schema, preserved the submitted business goal, and covered
              functional, emotional, and social jobs. Relevance scored 4.58/5.
            </p>
          </article>
          <article className="finding-risk">
            <span className="finding-label">What broke</span>
            <h4>Some hypotheses sounded too much like facts.</h4>
            <p>
              Unsupported-claim safety scored 2.67/5. Eight of 12 outputs contained frequency or
              magnitude language that required human review.
            </p>
          </article>
          <article className="finding-decision">
            <span className="finding-label">V0.2 decision</span>
            <h4>Make evidence quality part of every insight.</h4>
            <p>
              Add explicit hypothesis labels, evidence basis, confidence per item, and ranking by
              decision relevance—then rerun the same fixed cases.
            </p>
          </article>
        </div>
        <p className="evaluation-note">
          Internal baseline · 12 synthetic briefs · one reviewer · no claim of user or business
          impact. <a href="https://github.com/ftw10181-oss/ai-growth-agent/blob/main/evals/results/baseline-v0.1/report.md" target="_blank" rel="noreferrer">Read the full methodology and raw findings <span aria-hidden="true">↗</span></a>
        </p>
      </div>

      <div className="builder-card">
        <div>
          <span className="eyebrow">Built by Markus</span>
          <h3>Product strategy, workflow design, prompts, contracts, testing, and launch.</h3>
          <p>
            This independent project demonstrates the full AI product loop: scope a real problem,
            design the human–AI boundary, ship a working system, and define how quality will be measured.
          </p>
        </div>
        <a href="https://github.com/ftw10181-oss/ai-growth-agent" target="_blank" rel="noreferrer">
          View GitHub <span aria-hidden="true">↗</span>
        </a>
      </div>
    </section>
  );
}

export default function App() {
  const [brief, setBrief] = useState<GrowthBrief>(initialBrief);
  const [result, setResult] = useState<InsightResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = (key: keyof GrowthBrief, value: string) => {
    setBrief((current) => ({ ...current, [key]: value }));
  };

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      setResult(await generateInsight(brief));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header className="hero">
        <nav>
          <span className="brand-mark">AG</span><strong>AI Growth Agent</strong>
          <div className="nav-links">
            <a href="#demo">Try demo</a>
            <a href="#case-study">Case study</a>
            <a href="https://github.com/ftw10181-oss/ai-growth-agent" target="_blank" rel="noreferrer">GitHub ↗</a>
          </div>
          <span className="version">V0.2.1</span>
        </nav>
        <div className="hero-copy">
          <span className="eyebrow">From brief to testable hypotheses</span>
          <h1>See the user behind your growth goal.</h1>
          <p>Turn incomplete product context into structured jobs, pains, motivations, barriers, and research questions—before you jump to campaigns.</p>
          <div className="hero-actions">
            <a className="primary-action" href="#demo">Try the live workflow <span aria-hidden="true">↓</span></a>
            <a className="secondary-action" href="#case-study">Read the case study</a>
          </div>
        </div>
      </header>

      <section className="workspace" id="demo">
        <form onSubmit={handleSubmit}>
          <div className="form-heading">
            <div><span className="step">01</span><h2>Growth brief</h2></div>
            <p>Six fields. About two minutes.</p>
          </div>
          <div className="field-row">
            <label>Product<input value={brief.product} onChange={(event) => update("product", event.target.value)} minLength={2} maxLength={120} required /></label>
            <label>Target market<input value={brief.target_market} onChange={(event) => update("target_market", event.target.value)} minLength={2} maxLength={120} required /></label>
          </div>
          <label>Product description<textarea value={brief.product_description} onChange={(event) => update("product_description", event.target.value)} minLength={20} maxLength={2000} rows={3} required /></label>
          <div className="field-row">
            <label>Target audience<input value={brief.target_audience} onChange={(event) => update("target_audience", event.target.value)} minLength={5} maxLength={500} required /></label>
            <label>Business goal<select value={brief.business_goal} onChange={(event) => update("business_goal", event.target.value)}>{goals.map((goal) => <option key={goal}>{goal}</option>)}</select></label>
          </div>
          <label>Additional context <span className="optional">optional</span><textarea value={brief.additional_context} onChange={(event) => update("additional_context", event.target.value)} maxLength={2000} rows={3} /></label>
          <div className="submit-row">
            <p>No web research in V0.2.1. Every inferred insight is marked for validation.</p>
            <button disabled={loading}>{loading ? "Interpreting brief…" : "Generate user insight"}<span aria-hidden="true">→</span></button>
          </div>
          {error && <p className="error" role="alert">{error}</p>}
        </form>
        {result ? <Results result={result} /> : (
          <aside className="empty-state">
            <span className="step">02</span>
            <h2>Your insight map will appear here.</h2>
            <p>The agent first interprets your context, then generates hypotheses you can take into interviews and experiments.</p>
            <div className="pipeline"><span>Context</span><i>→</i><span>User insight</span><i>→</i><span>Validation</span></div>
          </aside>
        )}
      </section>
      <CaseStudy />
      <footer>
        <span>Built by Markus for overseas growth operators</span>
        <span>Structured · transparent · testable</span>
      </footer>
    </main>
  );
}
