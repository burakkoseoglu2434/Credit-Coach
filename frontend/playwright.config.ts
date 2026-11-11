import { defineConfig } from "@playwright/test";

const ci = !!process.env.CI;

export default defineConfig({
  testDir: "e2e",
  timeout: 60_000,
  retries: 0,
  reporter: ci ? [["list"]] : [["list"]],
  use: { baseURL: "http://127.0.0.1:4173", locale: "tr-TR", viewport: { width: 1200, height: 900 } },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
  webServer: [
    {
      command: "uv run uvicorn credit_coach.app:app --port 8000",
      cwd: "../backend",
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !ci,
      timeout: 120_000,
    },
    {
      command: "npm run build && npx vite preview --host 127.0.0.1 --port 4173 --strictPort",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: !ci,
      timeout: 120_000,
    },
  ],
});
