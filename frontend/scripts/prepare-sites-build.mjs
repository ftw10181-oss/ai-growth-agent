import { cp, mkdir } from "node:fs/promises";

await mkdir("dist/server", { recursive: true });
await cp("dist/ai_growth_agent_frontend/index.js", "dist/server/index.js");
