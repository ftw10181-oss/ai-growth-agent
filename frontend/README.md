# Frontend · V0.5

React 19, TypeScript 7, Vite 8, and a Cloudflare Pages Worker power the complete AI Growth Agent V0.5 product surface.

Both public entries render the same interface:

- `/` — project homepage, V0.5 release story, live workflow, and product case
- `/demo` — standalone route using the same V0.5 interface and API contract

This shared entry prevents the demo from drifting to an older workflow version.

## Local development

```bash
npm install
npm run dev
npm run typecheck
npm run lint:js
npm run build
```

When `VITE_API_BASE_URL` is set, the browser can call a separate FastAPI service. In the production artifact, the bundled Worker exposes a same-origin `POST /api/v5/research-strategy` endpoint.

## V0.5 streaming boundary

The Worker:

1. validates the six-field growth brief;
2. applies per-visitor and global usage protection;
3. calls the Dify Workflow app with a server-side `DIFY_API_KEY`;
4. proxies the upstream event stream without buffering;
5. never exposes the credential to browser code.

The browser waits for a successful `workflow_finished` event, validates all nine required outputs, and assembles the public `ResearchStrategyResponse`. An incomplete or failed workflow remains a visible error.

## Interface modules

- V0.5 release overview and research pipeline
- Growth Brief form and live research state
- Strategy decision summary
- Evidence Board with coverage, findings, sources, limitations, and gaps
- Eight-part research-quality review
- Context, User Insight, Market Hypothesis, and Value Proposition modules
- Validation priorities, risks, experiments, and source references
- Product case, responsible-AI boundary, architecture, and evaluation story

## Production settings

Keep `DIFY_API_KEY` as a Cloudflare Pages production secret. Optional public budget controls are:

- `LIVE_DAILY_LIMIT`
- `LIVE_PER_VISITOR_DAILY_LIMIT`
- `LIVE_MIN_INTERVAL_SECONDS`
- `LIVE_CACHE_TTL_SECONDS`

The counters and cache are best-effort per Worker isolate. Use a Durable Object or another shared store when strict cross-instance accounting is required.

## Cloudflare Pages

```bash
npm run preview:pages
npm run deploy:pages
```

`npm run build` compiles the client and Worker, then copies the Worker bundle to `dist/client/_worker.js` for Pages Advanced Mode.
