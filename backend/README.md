# Backend

FastAPI product boundary for the AI Growth Agent. Run in `mock` mode for the credential-free portfolio demo or `dify` mode to proxy the published workflow.

The V0.3 strategy endpoint is `POST /api/v3/strategy`. The existing `POST /api/analyze`, `POST /api/v2/insights`, and `POST /api/v1/insights` paths remain available for the V0.2 User Insight experience.

`/api/v3/strategy` returns Context, User Insight, Market Hypothesis, Value Proposition, a four-decision summary, and a deterministic cross-module quality review. The review validates source paths, evidence inheritance, market-claim grounding, decision continuity, product support, and validation testability.

```bash
pip install -r requirements-dev.txt
pytest
uvicorn app.main:app --reload
```

Configuration is documented in `.env.example`. Do not commit `.env` or expose the Dify application key to the frontend.

## Live-demo protection

`dify` mode includes conservative defaults for a public portfolio launch:

- 50 live workflow calls per UTC day
- 2 live calls per visitor per UTC day
- 60 seconds between live calls from the same visitor
- 24-hour cache for identical briefs
- automatic mock fallback when a quota is exhausted or Dify is unavailable

Configure these with `LIVE_DAILY_LIMIT`, `LIVE_PER_VISITOR_DAILY_LIMIT`,
`LIVE_MIN_INTERVAL_SECONDS`, `LIVE_CACHE_TTL_SECONDS`, and
`LIVE_FALLBACK_TO_MOCK`. A value of `0` disables the corresponding numeric
limit.

The built-in counters are process-local and are intended for a single-instance
portfolio deployment. Use a shared Redis/KV/Durable Object counter, plus a hard
provider spending limit, before horizontally scaling the live service.
