import { defineConfig, devices } from "@playwright/test";

const runId = Date.now();

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://127.0.0.1:3100", trace: "on-first-retry" },
  webServer: [
    {
      command: `cross-env FINANCE_COPILOT_DATABASE=web/test-results/e2e-${runId}.db FINANCE_COPILOT_VECTOR_DB=web/test-results/e2e-vectors-${runId}.db python -m uvicorn finance_copilot.interfaces.api.app:app --port 8100`,
      cwd: "..",
      url: "http://127.0.0.1:8100/api/v1/context",
      reuseExistingServer: false,
    },
    {
      command: "cross-env NEXT_PUBLIC_API_MODE=http NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8100 next dev --port 3100",
      url: "http://127.0.0.1:3100",
      reuseExistingServer: false,
    },
  ],
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
