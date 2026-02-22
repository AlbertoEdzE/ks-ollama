import { test, expect } from '@playwright/test'
import fs from 'node:fs'

const artifacts = 'test-artifacts'
function ensureDir() { try { fs.mkdirSync(artifacts, { recursive: true }) } catch { /* ignore */ } }

test('frontend landing screenshot', async ({ page }) => {
  ensureDir()
  const base = process.env.FRONTEND_BASE || 'http://localhost:5173/'
  await page.goto(base, { waitUntil: 'networkidle' })
  await expect(page.getByText('User Management')).toBeVisible()
  await page.screenshot({ path: `${artifacts}/landing.png`, fullPage: true })
})

test('api docs screenshot', async ({ page }) => {
  ensureDir()
  const docs = process.env.DOCS_URL || 'http://host.docker.internal:8080/docs'
  await page.goto(docs, { waitUntil: 'networkidle' })
  await expect(page.getByText(/Swagger UI|OpenAPI/i)).toBeVisible()
  await page.screenshot({ path: `${artifacts}/docs.png`, fullPage: true })
})
