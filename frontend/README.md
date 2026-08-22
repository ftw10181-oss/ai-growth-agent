# Frontend

React/Vite portfolio interface for AI Growth Agent V0.3.

```bash
npm install
cp .env.example .env
npm run dev
```

Locally, the primary interface calls the FastAPI service at `VITE_API_BASE_URL`.
The hosted Worker exposes the same-origin `/api/v3/strategy` boundary and keeps
the Dify key out of browser code and Git.

When deployed with the bundled Worker, keep `DIFY_API_KEY` as a server-side
secret. The Worker accepts the same `LIVE_DAILY_LIMIT`,
`LIVE_PER_VISITOR_DAILY_LIMIT`, `LIVE_MIN_INTERVAL_SECONDS`,
`LIVE_CACHE_TTL_SECONDS`, and `LIVE_FALLBACK_TO_MOCK` settings as the FastAPI
service. It falls back to a deterministic mock response when the live service
is unavailable or a daily quota has been reached.

The V0.3 result surface presents the decision summary, Context Interpreter,
User Insight, Market Hypothesis, Value Proposition, validation priorities,
source references, and six-part deterministic quality review. The standalone
`/demo` route remains available as the earlier evidence-aware insight showcase.

Worker counters and cache entries are best-effort per isolate. For a strict
cross-instance budget, back them with a Durable Object or another shared store
and set a hard limit with the model provider.
