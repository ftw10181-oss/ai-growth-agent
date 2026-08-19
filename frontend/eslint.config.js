// ESLint is intentionally limited to plain-JS configuration files.
//
// This project runs on TypeScript 7 (the native "tsgo" compiler), which does not
// yet expose the stable programmatic API that `typescript-eslint` requires
// (tracking: typescript-eslint issue #12518, marked "not planned" until TS 7.1).
// ESLint's own TS parser is blocked the same way (ESLint core issue #21070).
//
// Therefore TypeScript source linting is provided by `tsc` itself via
// `noUnusedLocals` + `noUnusedParameters` (see tsconfig.app.json) and enforced
// by the `npm run typecheck` script in CI. ESLint here guards the repo's
// JavaScript config files only.
import js from "@eslint/js";
import globals from "globals";

export default [
  {
    ignores: ["**/*.{ts,tsx}", "dist", "public", "node_modules"],
  },
  js.configs.recommended,
  {
    files: ["**/*.{js,mjs,cjs}"],
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.browser,
      },
    },
  },
];
