import { defineConfig, devices } from '@playwright/test'

declare const process: any

const useExternalServer = !!process.env.USE_EXTERNAL_SERVER

export default defineConfig({
  testDir: './tests',
  use: {
    baseURL: process.env.FRONTEND_BASE || 'http://localhost:5173',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } }
  ],
  webServer: useExternalServer
    ? undefined
    : {
        command: 'npm run build && npm run preview',
        url: 'http://localhost:5173',
        reuseExistingServer: !process.env.CI
      }
})
