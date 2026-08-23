# Frontend

React/Vite portfolio interface for AI Growth Agent V0.5.

```bash
npm install
cp .env.example .env
npm run dev
```

Locally, the primary interface calls the FastAPI service at `VITE_API_BASE_URL`.
The hosted Worker exposes the same-origin `/api/v5/research-strategy` boundary and keeps
the Dify key out of browser code and Git.

When deployed with the bundled Worker, keep `DIFY_API_KEY` as a server-side
secret. The Worker accepts the same `LIVE_DAILY_LIMIT`,
`LIVE_PER_VISITOR_DAILY_LIMIT`, `LIVE_MIN_INTERVAL_SECONDS`,
`LIVE_CACHE_TTL_SECONDS`, and `LIVE_FALLBACK_TO_MOCK` settings as the FastAPI
service. It falls back to a deterministic mock response when the live service
is unavailable or a daily quota has been reached.

The V0.5 result surface adds an Evidence Board with research coverage, source
links, confidence, limitations, research gaps, and an eight-part deterministic
quality review. It retains the V0.3 decision summary, Context Interpreter, User
Insight, Market Hypothesis, Value Proposition, and validation priorities. The standalone
`/demo` route remains available as the earlier evidence-aware insight showcase.

The V0.5 Worker opens Dify's streaming workflow mode and immediately proxies
the event stream to the browser. The browser assembles the typed public report
from the final workflow event, so the edge Worker does not remain active for
the full multi-step research run or hit the short execution boundary.

Worker counters and cache entries are best-effort per isolate. For a strict
cross-instance budget, back them with a Durable Object or another shared store
and set a hard limit with the model provider.
