import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

// Unit tests for the frontend's pure logic (no browser, no network): `npm test`.
export default defineConfig({
  resolve: { alias: { "@": fileURLToPath(new URL("./", import.meta.url)) } },
  test: { include: ["**/*.test.ts"], exclude: ["node_modules/**", ".next/**"], environment: "node" },
});
