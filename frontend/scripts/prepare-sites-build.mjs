import { cp, mkdir } from "node:fs/promises";

// Cloudflare Pages (Advanced mode): a single-file Worker placed at the root of
// the static output directory is picked up automatically and handles every
// route (including /api/analyze, /health and /demo). The Worker compiled by
// @cloudflare/vite-plugin is self-contained, so a straight copy is enough.
await cp("dist/ai_growth_agent_frontend/index.js", "dist/client/_worker.js");

// Keep the standalone server copy used by `vite preview` for local runs.
await mkdir("dist/server", { recursive: true });
await cp("dist/ai_growth_agent_frontend/index.js", "dist/server/index.js");
