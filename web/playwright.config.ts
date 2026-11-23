import { defineConfig, devices } from "@playwright/test";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import moduleAlias from "module";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Ensure node_modules inside web/ can be resolved by tests located in ../tests/e2e
const webNodeModules = path.resolve(__dirname, "node_modules");
if (process.env.NODE_PATH) {
  process.env.NODE_PATH = `${webNodeModules}:${process.env.NODE_PATH}`;
} else {
  process.env.NODE_PATH = webNodeModules;
}
// @ts-expect-error Node internal method to re-initialize module search paths
if (typeof moduleAlias._initPaths === "function") {
  // @ts-expect-error Node internal method to re-initialize module search paths
  moduleAlias._initPaths();
}

const envPath = path.resolve(__dirname, "../.env");
if (fs.existsSync(envPath)) {
  const content = fs.readFileSync(envPath, "utf-8");
  for (const line of content.split("\n")) {
    const trimmed = line.trim();
    if (trimmed && !trimmed.startsWith("#") && trimmed.includes("=")) {
      const idx = trimmed.indexOf("=");
      const key = trimmed.slice(0, idx).trim();
      const val = trimmed.slice(idx + 1).trim();
      if (!process.env[key]) {
        process.env[key] = val;
      }
    }
  }
}

export default defineConfig({
  testDir: "../tests/e2e",
  timeout: 30000,
  expect: {
    timeout: 5000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"], ["json", { outputFile: "../docs/results/playwright-results.json" }]],
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://localhost:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
