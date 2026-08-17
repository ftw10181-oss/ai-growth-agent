# AI Growth Agent

Turn a fuzzy overseas growth brief into a structured, actionable user insight.

AI Growth Agent is a portfolio-grade MVP for growth operators working on AI, SaaS, and consumer technology products. V0.1 covers the first slice of the product journey:

**[Open the live portfolio demo](https://ai-growth-agent-portfolio.markus12138467907.chatgpt.site)**

```text
Start → Context Interpreter → User Insight → Structured Output
```

The system does not claim to perform live market research. It transforms user-provided context into explicit hypotheses that a growth operator can validate.

## What V0.1 delivers

- Six-field growth brief with validation
- Context normalization before analysis
- Structured user insight: JTBD, pains, motivations, barriers, and scenarios
- Dify workflow build guide, prompts, and JSON schemas
- FastAPI adapter with a no-key demo mode and a Dify-connected mode
- Public React/Vite demo with a server-side Dify integration
- Sample request and output for recruiters and reviewers

## Product demo flow

1. A growth operator describes a product, market, audience, and business goal.
2. Context Interpreter turns uneven input into a concise analysis brief and records assumptions.
3. User Insight produces evidence-aware hypotheses rather than invented market facts.
4. The UI renders the response as scan-friendly insight cards.

## Repository map

```text
.
├── backend/                 FastAPI service and Dify adapter
├── demo/sample-output/      Portfolio-ready example
├── dify/
│   ├── prompts/             Versioned node prompts
│   ├── schemas/             Structured-output contracts
│   └── workflow-v0.1.md     Exact canvas setup
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

Import [dify/workflow-v0.1.yml](dify/workflow-v0.1.yml), select a model available in your workspace, test, and publish. If the imported provider cannot be resolved, use [dify/workflow-v0.1.md](dify/workflow-v0.1.md) to build the same canvas manually. Then update `backend/.env`:

```dotenv
APP_MODE=dify
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_API_KEY=app-your-workflow-key
```

Keep the Dify key on the backend only. The browser never calls Dify directly.

## API contract

`POST /api/analyze`

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

V0.1 is successful when a new user can submit a brief, receive valid structured output, understand which statements are assumptions, and identify at least three interview or experiment directions in under three minutes.

## Roadmap

- V0.2: market-hypothesis and value-proposition modules
- V0.3: content strategy and growth experiments
- V0.4: web research with citations and evidence grading
- V1.0: saved projects, comparison, export, and evaluation dashboard

## Responsible AI choices

- No claim of real-time research in V0.1
- Assumptions are returned explicitly
- Prompts prohibit fabricated statistics, quotes, and competitor facts
- Pydantic and JSON Schema validate the workflow boundary
- A deterministic demo response keeps the portfolio reviewable without credentials

## License

MIT — see [LICENSE](LICENSE).
