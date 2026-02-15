// Code was generated via OCI AI and was reviewed by a human SDE
// Tag: #ai-assisted
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3005",
    trace: "on-first-retry"
  },
  webServer: {
    command: "npm run dev -- --port 3005",
    url: "http://127.0.0.1:3005",
    reuseExistingServer: true,
    timeout: 120000
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});
