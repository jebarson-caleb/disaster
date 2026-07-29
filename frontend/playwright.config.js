import { defineConfig, devices } from '@playwright/test';

const isCI = Boolean(globalThis.process?.env.CI);
const executablePath = globalThis.process?.env.PLAYWRIGHT_EXECUTABLE_PATH;

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  forbidOnly: isCI,
  retries: isCI ? 1 : 0,
  reporter: 'line',
  use: {
    baseURL: globalThis.process?.env.BASE_URL || 'http://127.0.0.1:4173',
    launchOptions: executablePath ? { executablePath } : undefined,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
