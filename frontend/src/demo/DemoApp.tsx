import { useCallback, useEffect, useState } from "react";
import { generateInsight } from "../api";
import type {
  BusinessGoal,
  GrowthBrief,
  InsightEvidence,
  InsightItem,
  InsightResponse,
} from "../types";

const GOALS: BusinessGoal[] = [
  "Brand Awareness",
  "User Acquisition",
  "Conversion",
  "Community Growth",
  "Product Launch",
  "Retention",
];

const DEFAULT_BRIEF: GrowthBrief = {
  product: "AI Translation Earbuds",
  product_description:
    "Real-time AI translation earbuds that let two people speak their own languages naturally.",
  target_market: "United States",
  target_audience: "Frequent international business travelers",
  business_goal: "User Acquisition",
  additional_context:
    "Entering the US market; test Reddit and TikTok. Competing with Pocketalk-style devices.",
};

/* ------------------------------------------------------------------ */
/*  Derived recommendation engine (frontend-only, no backend change)   */
/* ------------------------------------------------------------------ */

interface Recommendation {
  priority: "Act now" | "Validate first";
  title: string;
  detail: string;
}

function buildRecommendations(data: InsightResponse): Recommendation[] {
  const recs: Recommendation[] = [];

  // 1) Brief-backed, high-confidence insights → act directly
  const actable = collectItems(data).filter(
    (i) =>
      i.evidence?.basis === "explicit_brief" &&
      i.evidence.confidence === "high",
  );
  for (const item of actable.slice(0, 3)) {
    recs.push({
      priority: "Act now",
      title: item.insight,
      detail: item.why_it_matters,
    });
  }

  // 2) Primary-relevance, inference-based insights → validate before acting
  const validate = collectItems(data).filter(
    (i) =>
      i.decision_relevance === "primary" &&
      i.evidence?.validation_status === "needs_validation",
  );
  for (const item of validate.slice(0, 3)) {
    recs.push({
      priority: "Validate first",
      title: item.insight,
      detail: `${item.why_it_matters} — verify with real users before scaling spend.`,
    });
  }

  return recs;
}

function collectItems(data: InsightResponse): InsightItem[] {
  const u = data.user_insight;
  return [
    ...u.jobs_to_be_done.map((j) => ({
      insight: j.job,
      why_it_matters: j.why_it_matters,
      decision_relevance: j.decision_relevance,
      evidence: j.evidence,
    })),
    ...u.pain_points,
    ...u.purchase_motivations,
    ...u.adoption_barriers,
  ];
}

const BASIS_LABEL: Record<InsightEvidence["basis"], string> = {
  explicit_brief: "Brief",
  contextual_inference: "Inference",
  behavioral_hypothesis: "Hypothesis",
};

const CONFIDENCE_PCT: Record<InsightEvidence["confidence"], number> = {
  low: 38,
  medium: 64,
  high: 88,
};

const OVERALL_PCT: Record<InsightResponse["user_insight"]["confidence"], number> = {
  low: 38,
  medium: 64,
  high: 88,
};

/* ------------------------------------------------------------------ */
/*  Small presentational pieces                                        */
/* ------------------------------------------------------------------ */

function EvidenceBadge({ evidence }: { evidence?: InsightEvidence }) {
  if (!evidence) return <span className="ev-badge ev-badge--none">No evidence</span>;
  return (
    <span className={`ev-badge ev-badge--${evidence.basis}`}>
      {BASIS_LABEL[evidence.basis]} · {evidence.confidence}
    </span>
  );
}

function ConfidenceMeter({ pct, label }: { pct: number; label: string }) {
  const tone = pct >= 75 ? "high" : pct >= 55 ? "medium" : "low";
  return (
    <div className="meter">
      <div className="meter__head">
        <span className="meter__label">{label}</span>
        <span className={`meter__value meter__value--${tone}`}>{pct}%</span>
      </div>
      <div className="meter__track">
        <div className={`meter__fill meter__fill--${tone}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function InsightRow({ item }: { item: InsightItem }) {
  return (
    <li className="insight-row">
      <div className="insight-row__top">
        <span className="insight-row__text">{item.insight}</span>
        {item.decision_relevance === "primary" && (
          <span className="chip chip--primary">Primary</span>
        )}
        <EvidenceBadge evidence={item.evidence} />
      </div>
      <p className="insight-row__why">{item.why_it_matters}</p>
    </li>
  );
}

type SectionItem = Omit<InsightItem, "insight"> & {
  insight?: string;
  job?: string;
  dimension?: string;
};

function Section({
  title,
  subtitle,
  items,
}: {
  title: string;
  subtitle: string;
  items: SectionItem[];
}) {
  if (items.length === 0) return null;
  return (
    <section className="report-section">
      <div className="report-section__head">
        <h3>{title}</h3>
        <span className="report-section__sub">{subtitle}</span>
      </div>
      <ul className="insight-list">
        {items.map((item, i) => (
          <InsightRow
            key={`${title}-${i}`}
            item={
              {
                insight: item.job ?? item.insight,
                why_it_matters: item.why_it_matters,
                decision_relevance: item.decision_relevance,
                evidence: item.evidence,
              } as InsightItem
            }
          />
        ))}
      </ul>
    </section>
  );
}

/* ------------------------------------------------------------------ */
/*  Report                                                             */
/* ------------------------------------------------------------------ */

function Report({ data }: { data: InsightResponse }) {
  const u = data.user_insight;
  const recs = buildRecommendations(data);
  const overallPct = OVERALL_PCT[u.confidence];

  return (
    <div className="report">
      <header className="report__header">
        <div>
          <p className="eyebrow">Growth Insight Report</p>
          <h2>{u.target_user.primary_segment}</h2>
          <p className="report__rationale">{u.target_user.rationale}</p>
        </div>
        <div className="report__score">
          <div className="gauge" style={{ "--pct": `${overallPct * 3.6}deg` } as React.CSSProperties}>
            <span>{overallPct}%</span>
          </div>
          <p>Overall confidence</p>
        </div>
      </header>

      <div className="report__meta">
        <span className="chip">Goal: {data.context.primary_goal}</span>
        <span className="chip">Mode: {data.mode}</span>
        {data.quality_review && (
          <span className={`chip chip--${data.quality_review.status === "passed" ? "ok" : "warn"}`}>
            Quality: {data.quality_review.status.replaceAll("_", " ")}
          </span>
        )}
      </div>

      <div className="report__grid">
        <div className="report__col report__col--main">
          <Section
            title="Jobs to be done"
            subtitle="functional · emotional · social"
            items={u.jobs_to_be_done.map((j) => ({
              job: j.job,
              why_it_matters: j.why_it_matters,
              decision_relevance: j.decision_relevance,
              evidence: j.evidence,
            }))}
          />
          <Section title="Pain points" subtitle="what blocks the job" items={u.pain_points} />
          <Section
            title="Purchase motivations"
            subtitle="why they would buy"
            items={u.purchase_motivations}
          />
          <Section
            title="Adoption barriers"
            subtitle="what holds them back"
            items={u.adoption_barriers}
          />

          <section className="report-section">
            <div className="report-section__head">
              <h3>Recommendations</h3>
              <span className="report-section__sub">derived from evidence & decision relevance</span>
            </div>
            <ul className="rec-list">
              {recs.map((r, i) => (
                <li className={`rec rec--${r.priority === "Act now" ? "act" : "validate"}`} key={i}>
                  <span className="rec__tag">{r.priority}</span>
                  <div>
                    <p className="rec__title">{r.title}</p>
                    <p className="rec__detail">{r.detail}</p>
                  </div>
                </li>
              ))}
              {recs.length === 0 && <li className="rec rec--empty">No actionable items yet.</li>}
            </ul>
          </section>
        </div>

        <aside className="report__col report__col--side">
          <section className="side-card">
            <h4>Confidence by section</h4>
            <ConfidenceMeter pct={overallPct} label="Overall insight" />
            {u.jobs_to_be_done[0]?.evidence && (
              <ConfidenceMeter
                pct={CONFIDENCE_PCT[u.jobs_to_be_done[0].evidence.confidence]}
                label="Jobs to be done"
              />
            )}
            {u.pain_points[0]?.evidence && (
              <ConfidenceMeter
                pct={CONFIDENCE_PCT[u.pain_points[0].evidence.confidence]}
                label="Pain points"
              />
            )}
          </section>

          <section className="side-card">
            <h4>Evidence legend</h4>
            <ul className="legend">
              <li><span className="dot dot--explicit_brief" /> Brief — stated in your brief</li>
              <li><span className="dot dot--contextual_inference" /> Inference — derived from context</li>
              <li><span className="dot dot--behavioral_hypothesis" /> Hypothesis — needs user testing</li>
            </ul>
          </section>

          <section className="side-card">
            <h4>Validate next</h4>
            <ol className="q-list">
              {u.research_questions.slice(0, 3).map((q, i) => (
                <li key={i}>{q}</li>
              ))}
            </ol>
          </section>

          <section className="side-card">
            <h4>Assumptions to check</h4>
            <ul className="a-list">
              {u.assumptions_to_validate.map((a, i) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </section>
        </aside>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Form                                                               */
/* ------------------------------------------------------------------ */

function BriefForm({
  brief,
  onChange,
  onGenerate,
  busy,
}: {
  brief: GrowthBrief;
  onChange: (next: GrowthBrief) => void;
  onGenerate: () => void;
  busy: boolean;
}) {
  return (
    <form
      className="form"
      onSubmit={(e) => {
        e.preventDefault();
        onGenerate();
      }}
    >
      <label className="field">
        <span>Product</span>
        <input
          value={brief.product}
          onChange={(e) => onChange({ ...brief, product: e.target.value })}
          placeholder="AI Translation Earbuds"
        />
      </label>

      <label className="field">
        <span>What does it do?</span>
        <textarea
          value={brief.product_description}
          onChange={(e) => onChange({ ...brief, product_description: e.target.value })}
          rows={3}
          placeholder="One or two sentences on the product and how it works."
        />
      </label>

      <div className="field-row">
        <label className="field">
          <span>Target market</span>
          <input
            value={brief.target_market}
            onChange={(e) => onChange({ ...brief, target_market: e.target.value })}
            placeholder="United States"
          />
        </label>
        <label className="field">
          <span>Business goal</span>
          <select
            value={brief.business_goal}
            onChange={(e) =>
              onChange({ ...brief, business_goal: e.target.value as BusinessGoal })
            }
          >
            {GOALS.map((g) => (
              <option key={g} value={g}>
                {g}
              </option>
            ))}
          </select>
        </label>
      </div>

      <label className="field">
        <span>Target audience</span>
        <input
          value={brief.target_audience}
          onChange={(e) => onChange({ ...brief, target_audience: e.target.value })}
          placeholder="Frequent international business travelers"
        />
      </label>

      <label className="field">
        <span>Additional context</span>
        <textarea
          value={brief.additional_context}
          onChange={(e) => onChange({ ...brief, additional_context: e.target.value })}
          rows={3}
          placeholder="Channels to test, competitors, constraints…"
        />
      </label>

      <div className="form__actions">
        <button className="btn btn--primary" type="submit" disabled={busy}>
          {busy ? "Generating…" : "Generate report"}
        </button>
        <button
          className="btn btn--ghost"
          type="button"
          onClick={() => onChange({ ...DEFAULT_BRIEF })}
          disabled={busy}
        >
          Reset
        </button>
      </div>
    </form>
  );
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export function DemoApp() {
  const [brief, setBrief] = useState<GrowthBrief>(DEFAULT_BRIEF);
  const [data, setData] = useState<InsightResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = useCallback(async (nextBrief: GrowthBrief) => {
    setBusy(true);
    setError(null);
    try {
      const result = await generateInsight(nextBrief);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed.");
    } finally {
      setBusy(false);
    }
  }, []);

  // Auto-run once on mount so the page is screenshot-ready.
  useEffect(() => {
    void run(DEFAULT_BRIEF);
  }, [run]);

  return (
    <div className="page">
      <header className="topbar">
        <div className="topbar__brand">
          <span className="topbar__logo">◈</span>
          <div>
            <h1>AI Growth Agent</h1>
            <p>Evidence-aware user insight, from a fuzzy brief</p>
          </div>
        </div>
        <div className="topbar__right">
          <span className="chip chip--ok">v0.2.1</span>
          <a
            className="topbar__link"
            href="https://github.com/ftw10181-oss/ai-growth-agent"
            target="_blank"
            rel="noreferrer"
          >
            Source on GitHub ↗
          </a>
        </div>
      </header>

      <div className="stage">
        <aside className="stage__form">
          <div className="panel-head">
            <h2>Growth brief</h2>
            <p>Describe your product, market, and goal. The agent structures the rest.</p>
          </div>
          <BriefForm brief={brief} onChange={setBrief} onGenerate={() => void run(brief)} busy={busy} />

          <div className="howto">
            <h4>How to read the report</h4>
            <ul className="legend">
              <li><span className="dot dot--explicit_brief" /> Brief — directly supported by your input</li>
              <li><span className="dot dot--contextual_inference" /> Inference — derived, still testable</li>
              <li><span className="dot dot--behavioral_hypothesis" /> Hypothesis — needs validation</li>
            </ul>
          </div>
        </aside>

        <main className="stage__report">
          {error && (
            <div className="banner banner--error">
              <strong>Generation failed</strong> — {error}. Is the backend running? (
              <code>uvicorn app.main:app --reload</code> in <code>backend/</code>)
            </div>
          )}
          {busy && !data && <div className="skeleton">Analyzing brief…</div>}
          {data && <Report data={data} />}
        </main>
      </div>
    </div>
  );
}
