import { fileURLToPath } from "node:url";
import { sites } from "@openai/sites-vite-plugin";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const resolve = (path: string) => fileURLToPath(new URL(path, import.meta.url));

export default defineConfig(async () => {
  const { cloudflare } = await import("@cloudflare/vite-plugin");

  return {
    // Multi-Page App mode: Vite auto-discovers index.html + demo.html.
    appType: "mpa" as const,
    plugins: [
      react(),
      sites(),
      cloudflare({
        config: {
          main: "./worker/index.ts",
          compatibility_flags: ["nodejs_compat"],
        },
      }),
    ],
    server: { port: 5173 },
    environments: {
      // Scope the HTML entry points to the client environment only, so the
      // Worker build (ai_growth_agent_frontend) is not affected.
      client: {
        build: {
          rollupOptions: {
            input: {
              main: resolve("index.html"),
              demo: resolve("demo.html"),
            },
          },
        },
      },
    },
  };
});
