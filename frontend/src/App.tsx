import { FormEvent, useState } from "react";
import { generateInsight } from "./api";
import type { BusinessGoal, GrowthBrief, InsightItem, InsightResponse } from "./types";

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

function InsightList({ items }: { items: InsightItem[] }) {
  return (
    <ul className="insight-list">
      {items.map((item, index) => (
        <li key={`${item.insight}-${index}`}>
          <p>{item.insight}</p>
          <small>{item.why_it_matters}</small>
        </li>
      ))}
    </ul>
  );
}

function Results({ result }: { result: InsightResponse }) {
  const insight = result.user_insight;
  return (
    <section className="results" aria-live="polite">
      <div className="results-header">
        <div>
          <span className="eyebrow">User Insight · V0.1</span>
          <h2>{insight.target_user.primary_segment}</h2>
          <p>{insight.target_user.rationale}</p>
        </div>
        <span className={`confidence confidence-${insight.confidence}`}>{insight.confidence} confidence</span>
      </div>

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
                <span>{item.dimension}</span>
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
        <nav><span className="brand-mark">AG</span><strong>AI Growth Agent</strong><span className="version">V0.1</span></nav>
        <div className="hero-copy">
          <span className="eyebrow">From brief to testable hypotheses</span>
          <h1>See the user behind your growth goal.</h1>
          <p>Turn incomplete product context into structured jobs, pains, motivations, barriers, and research questions—before you jump to campaigns.</p>
        </div>
      </header>

      <section className="workspace">
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
            <p>No web research in V0.1. Output is designed for validation.</p>
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
      <footer><span>Built for overseas growth operators</span><span>Structured · transparent · testable</span></footer>
    </main>
  );
}
