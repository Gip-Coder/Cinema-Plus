import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/__tests__/setup.ts",
    exclude: ["node_modules/**", ".next/**", "scripts/**", "e2e/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json", "html"],
      reportsDirectory: "./reports/coverage/frontend",
      exclude: ["node_modules/**", ".next/**", "scripts/**", "e2e/**", "vitest.config.ts", "next.config.ts"],
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
