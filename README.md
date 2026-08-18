<p align="center">
  <img src="docs/assets/ai-growth-agent-banner.jpg" alt="AI Growth Agent — from fuzzy growth briefs to testable user insights" width="100%" />
</p>

<p align="center">
  <strong>An evidence-aware AI workflow for growth operators working on AI, SaaS, and consumer technology products.</strong>
</p>

<p align="center">
  <a href="https://ai-growth-agent-portfolio.markus12138467907.chatgpt.site"><strong>Live Demo</strong></a>
  ·
  <a href="docs/architecture.md">Architecture</a>
  ·
  <a href="evals/README.md">Evaluation</a>
  ·
  <a href="demo/sample-output/user-insight.json">Sample Output</a>
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-v0.2.1-4f46e5" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-3776ab" />
  <img alt="React" src="https://img.shields.io/badge/React-19-149eca" />
  <img alt="License" src="https://img.shields.io/badge/license-MIT-16a34a" />
</p>

## The product

AI Growth Agent turns an uneven product brief into structured user-insight hypotheses—JTBD, pains, motivations, barriers, and usage scenarios—while making assumptions, evidence quality, and validation needs explicit.

```text
Growth brief → Context Interpreter → User Insight → Safe-wording revision → Quality Gate
```

The system deliberately does **not** claim to perform live market research. It transforms user-provided context into hypotheses that a growth operator can validate.

## Why it matters

- **Useful, not theatrical:** output is designed for decisions and follow-up research, not generic AI prose.
- **Evidence-aware by default:** every insight records its basis, confidence, validation status, and decision relevance.
- **Reviewable without credentials:** the public demo and deterministic mock mode expose the full product journey safely.

## What V0.2.1 delivers

- Six-field growth brief with validation
- Context normalization before analysis
- Structured user insight: JTBD, pains, motivations, barriers, and scenarios
- Evidence basis, per-item confidence, validation status, and decision relevance
- Deterministic post-generation quality gate for structure, evidence, research questions, and claim language
- Transparent safe-wording revision that preserves the original claim while marking it as a hypothesis
- Separate `passed`, `passed_with_notes`, and `review_required` outcomes so soft warnings do not look like system failures
- Dify workflow build guide, prompts, and JSON schemas
- FastAPI adapter with a no-key demo mode and a Dify-connected mode
- Public React/Vite demo with a server-side Dify integration
- Sample request and output for recruiters and reviewers

## Product demo flow

1. A growth operator describes a product, market, audience, and business goal.
2. Context Interpreter turns uneven input into a concise analysis brief and records assumptions.
3. User Insight produces evidence-aware hypotheses rather than invented market facts.
4. A deterministic server layer prefixes unsupported causal or comparative wording with `Hypothesis to test —`.
5. The quality gate checks the revised output independently of the model and separates blockers from review notes.
6. The UI renders the insight cards, the automatic revision count, and any remaining review notes.

## Repository map

```text
.
├── backend/                 FastAPI service and Dify adapter
├── demo/sample-output/      Portfolio-ready example
├── evals/                   Fixed cases, rubric, user-test guide, scorecard
├── dify/
│   ├── prompts/             Versioned node prompts
│   ├── schemas/             Structured-output contracts
│   ├── workflow-v0.1.yml    Reproducible evaluation baseline
│   └── workflow-v0.2.yml    Evidence-aware workflow candidate
├── docs/                    PRD, architecture, and product decisions
└── frontend/                React + TypeScript demo UI
```

## Run locally

Prerequisites: Python 3.11+ and Node.js 20+.

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The default `APP_MODE=mock` is intentional: the full product journey runs without exposing an API key. API docs are available at `http://localhost:8000/docs`.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open `http://localhost:5173` and submit the pre-filled example.

### 3. Connect Dify

Import [dify/workflow-v0.2.yml](dify/workflow-v0.2.yml), select a model available in your workspace, test, and publish. If the imported provider cannot be resolved, use [dify/workflow-v0.2.md](dify/workflow-v0.2.md) to build the same canvas manually. Then update `backend/.env`:

```dotenv
APP_MODE=dify
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_API_KEY=app-your-workflow-key
```

Keep the Dify key on the backend only. The browser never calls Dify directly.

## API contract

`POST /api/analyze`

`POST /api/v2/insights` is the versioned V0.2 contract route; V0.2.1 is a compatible safety-layer update.

`POST /api/v1/insights` remains available as a compatibility alias.

```json
{
  "product": "AI Translation Earbuds",
  "product_description": "Real-time AI translation earbuds for cross-language communication.",
  "target_market": "United States",
  "target_audience": "Frequent international business travelers",
  "business_goal": "User Acquisition",
  "additional_context": "Entering the US market; test Reddit and TikTok."
}
```

See [demo/sample-output/user-insight.json](demo/sample-output/user-insight.json) for the full response.

## Success criteria

V0.2.1 is successful when a new user can submit a brief, receive valid structured output, distinguish brief evidence from inference, see risky claims reframed as hypotheses, and identify any remaining review notes in under three minutes.

## Evaluation system

The repository includes a repeatable evaluation system rather than relying on a single polished example:

- 12 fixed briefs covering six business goals and multiple product categories
- Boundary cases for sparse context, goal conflict, and unfamiliar domains
- Hard contract gates plus a five-dimension human scoring rubric
- A counterbalanced five-participant moderated user-test plan
- An offline checker for schema, goal consistency, JTBD dimensions, and claim-risk flags

See [evals/README.md](evals/README.md).

### V0.1 live baseline

The published Dify workflow completed **12/12 cases successfully** with **100% schema, goal-consistency, JTBD-dimension, and item-count compliance**. Median end-to-end latency was **21.5 seconds** across 35,371 model tokens.

The single-reviewer content score was **3.75/5**. Relevance was strongest at **4.58/5**; unsupported-claim safety was the main weakness at **2.67/5**, because inferred behaviors were sometimes phrased as facts. Only 2/12 cases met the full publish threshold. V0.2 directly addresses that finding with a mandatory evidence contract on every insight item.

These are internal synthetic-case results—not user research or evidence of business impact. See the [baseline report](evals/results/baseline-v0.1/report.md) and [completed scorecard](evals/results/baseline-v0.1/scorecard.csv).

## Roadmap

- V0.2.1: evidence-aware insight, deterministic safe-wording revision, and clearer quality states
- V0.3: market hypothesis and value proposition
- V0.4: content strategy and growth experiments
- V0.5: web research with citations and evidence grading
- V1.0: saved projects, comparison, export, and evaluation dashboard

## Responsible AI choices

- No claim of real-time research in V0.2.1
- Assumptions are returned explicitly
- Every JTBD and insight records evidence basis, confidence, validation status, and decision relevance
- Prompts prohibit fabricated statistics, quotes, and competitor facts
- Pydantic and JSON Schema validate the workflow boundary
- The server records every automatic wording revision; it adds an explicit hypothesis marker without deleting or inventing substantive content
- Only structure or evidence failures are blocking; research-pattern and claim-language findings remain visible as review notes
- A deterministic post-generation review makes risky wording and weak research questions visible instead of silently accepting them
- A deterministic demo response keeps the portfolio reviewable without credentials

## License

MIT — see [LICENSE](LICENSE).
