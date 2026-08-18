# Frontend

React/Vite portfolio interface for AI Growth Agent.

```bash
npm install
cp .env.example .env
npm run dev
```

The frontend expects the FastAPI service at `VITE_API_BASE_URL`. It never stores or calls with a Dify API key.

When deployed with the bundled Worker, keep `DIFY_API_KEY` as a server-side
secret. The Worker accepts the same `LIVE_DAILY_LIMIT`,
`LIVE_PER_VISITOR_DAILY_LIMIT`, `LIVE_MIN_INTERVAL_SECONDS`,
`LIVE_CACHE_TTL_SECONDS`, and `LIVE_FALLBACK_TO_MOCK` settings as the FastAPI
service. It falls back to a deterministic mock response when the live service
is unavailable or a daily quota has been reached.

Worker counters and cache entries are best-effort per isolate. For a strict
cross-instance budget, back them with a Durable Object or another shared store
and set a hard limit with the model provider.
