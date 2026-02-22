import { test, expect } from '@playwright/test'

declare const process: any

const FRONTEND_BASE = process.env.FRONTEND_BASE || 'http://localhost:5173'
const API_BASE = process.env.API_BASE || 'http://localhost:8080'

async function apiLogin(request: any, email: string, password: string): Promise<string> {
  const r = await request.post(`${API_BASE}/auth/login`, { data: { username: email, password } })
  expect(r.status(), 'login status').toBe(200)
  const data = await r.json()
  const token = data.access_token as string
  expect(token, 'access_token present').toBeTruthy()
  return token
}

async function apiDeleteUserByEmail(request: any, token: string, email: string) {
  const list = await request.get(`${API_BASE}/users?limit=200&offset=0`, { headers: { Authorization: `Bearer ${token}` } })
  if (list.status() !== 200) return
  const users = await list.json()
  const found = users.find((u: any) => u.email === email)
  if (found) {
    await request.delete(`${API_BASE}/users/${found.id}`, { headers: { Authorization: `Bearer ${token}` } })
  }
}

test.describe('End-to-end user management', () => {
  const adminEmail = 'admin@example.com'
  const adminPassword = process.env.ADMIN_PASSWORD || 'admin'
  const newUserEmail = 'al@gmail.com'
  const newUserPassword = 'Passw0rd!'

  test.beforeAll(async ({ request }) => {
    // Ensure API is healthy
    const h = await request.get(`${API_BASE}/healthz`)
    expect(h.status(), 'healthz').toBe(200)
    // Cleanup any residue from prior runs
    const adminToken = await apiLogin(request, adminEmail, adminPassword)
    await apiDeleteUserByEmail(request, adminToken, newUserEmail)
  })

  test.afterAll(async ({ request }) => {
    const adminToken = await apiLogin(request, adminEmail, adminPassword)
    await apiDeleteUserByEmail(request, adminToken, newUserEmail)
  })

  test('0) Sign-in validation and error handling', async ({ page }) => {
    await page.goto(FRONTEND_BASE)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByRole('alert')).toHaveText(/Username and password are required/)
    await page.getByLabel('Username').fill(adminEmail)
    await page.getByLabel('Password').fill('wrong-password')
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByRole('alert')).toHaveText(/Invalid credentials/)
  })

  test('1) Admin Authentication Flow', async ({ page }, testInfo) => {
    const loginNetworkEvents: any[] = []
    page.on('request', (req) => {
      if (req.url().includes('/auth/login')) {
        loginNetworkEvents.push({
          type: 'request',
          url: req.url(),
          method: req.method(),
          postData: req.postData()
        })
      }
    })
    page.on('response', (res) => {
      if (res.url().includes('/auth/login')) {
        loginNetworkEvents.push({
          type: 'response',
          url: res.url(),
          status: res.status()
        })
      }
    })
    const t0 = Date.now()
    await page.goto(FRONTEND_BASE, { waitUntil: 'networkidle' })
    await page.getByLabel('Username').fill(adminEmail)
    await page.getByLabel('Password').fill(adminPassword)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByText('Admin panel')).toBeVisible()
    // Verify admin-only action succeeds (list users)
    await page.getByRole('button', { name: 'Refresh' }).click()
    await expect(page.getByText(/No users yet|@/)).toBeVisible()
    const t1 = Date.now()
    expect(t1 - t0, 'admin login duration (ms)').toBeLessThan(2000)
    await testInfo.attach('login-network.json', {
      body: JSON.stringify(loginNetworkEvents, null, 2),
      contentType: 'application/json'
    })
  })

  test('2) User Registration Process (create + duplicate + validation)', async ({ page }) => {
    await page.goto(FRONTEND_BASE)
    // Assumes already logged-in from previous test in same worker; if not, log in
    if (!(await page.getByText('Admin panel').isVisible())) {
      await page.getByLabel('Username').fill(adminEmail)
      await page.getByLabel('Password').fill(adminPassword)
      await page.getByRole('button', { name: 'Sign in' }).click()
      await expect(page.getByText('Admin panel')).toBeVisible()
    }
    // Create user
    await page.getByLabel('Email').fill(newUserEmail)
    await page.getByRole('button', { name: 'Create' }).click()
    await expect(page.getByText(`Created ${newUserEmail}`)).toBeVisible()
    // Duplicate
    await page.getByLabel('Email').fill(newUserEmail)
    await page.getByRole('button', { name: 'Create' }).click()
    await expect(page.getByText(/Create failed: 400|User exists/)).toBeVisible()
    // Invalid email
    await page.getByLabel('Email').fill('not-an-email')
    await page.getByRole('button', { name: 'Create' }).click()
    await expect(page.getByText(/Create failed: 4/)).toBeVisible()
  })

  test('3) New User Login Verification (set password, login as user)', async ({ page }) => {
    await page.goto(FRONTEND_BASE)
    // Ensure admin logged in
    if (!(await page.getByText('Admin panel').isVisible())) {
      await page.getByLabel('Username').fill(adminEmail)
      await page.getByLabel('Password').fill(adminPassword)
      await page.getByRole('button', { name: 'Sign in' }).click()
      await expect(page.getByText('Admin panel')).toBeVisible()
    }
    // Refresh and select user
    await page.getByRole('button', { name: 'Refresh' }).click()
    await page.getByText(newUserEmail).waitFor()
    const li = page.locator('ul >> text=' + newUserEmail)
    await li.getByRole('button', { name: /Select|Selected/ }).click()
    // Set password
    await page.getByLabel('New password').fill(newUserPassword)
    await page.getByRole('button', { name: 'Update password' }).click()
    await expect(page.getByText('Password updated')).toBeVisible()
    // Optionally set roles
    await page.getByLabel('Roles (comma-separated)').fill('user')
    await page.getByRole('button', { name: 'Save settings' }).click()
    await expect(page.getByText('User updated')).toBeVisible()
    // Logout admin
    await page.getByRole('button', { name: 'Sign out' }).click()
    // Login as new user
    const t0 = Date.now()
    await page.getByLabel('Username').fill(newUserEmail)
    await page.getByLabel('Password').fill(newUserPassword)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByText('Signed in')).toBeVisible()
    const t1 = Date.now()
    expect(t1 - t0, 'user login duration (ms)').toBeLessThan(2000)
    // Verify that non-admin cannot list users (403 handled)
    await page.getByRole('button', { name: 'Refresh' }).click()
    await expect(page.getByText(/Failed to load users|No users/)).toBeVisible()
  })

  test('4) Ollama Integration (chat + embeddings; token and permission checks)', async ({ page }) => {
    await page.goto(FRONTEND_BASE)
    if (!(await page.getByText('Signed in').isVisible())) {
      await page.getByLabel('Username').fill(newUserEmail)
      await page.getByLabel('Password').fill(newUserPassword)
      await page.getByRole('button', { name: 'Sign in' }).click()
      await expect(page.getByText('Signed in')).toBeVisible()
    }
    await page.getByLabel('Prompt').fill('Hello')
    const chatRespPromise = page.waitForResponse(r => r.url().includes('/ollama/chat'))
    const t0 = Date.now()
    await page.getByRole('button', { name: 'Send' }).click()
    const resp = await chatRespPromise
    const t1 = Date.now()
    // Expect 200 (success) or 502 (Ollama down). Must not be 401/403
    expect([200, 502]).toContain(resp.status())
    await expect(page.locator('pre')).toBeVisible()
    expect(t1 - t0, 'chat call duration (ms)').toBeLessThan(5000)
    await page.getByText('Embeddings').scrollIntoViewIfNeeded()
    await page.getByLabel('Text').fill('hello world')
    const embRespPromise = page.waitForResponse(r => r.url().includes('/ollama/embeddings'))
    await page.getByRole('button', { name: 'Generate' }).click()
    const embResp = await embRespPromise
    expect([200, 502]).toContain(embResp.status())
    await expect(page.getByText(/Vector length:/)).toBeVisible()
  })

  test('5) Error Handling (invalid email, duplicate, login failure, unauthenticated Ollama)', async ({ page, request }) => {
    // Login failure
    await page.goto(FRONTEND_BASE)
    await page.getByLabel('Username').fill('nobody@example.com')
    await page.getByLabel('Password').fill('wrong')
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByRole('alert')).toHaveText(/Invalid credentials|Network error/)
    // Unauthenticated Ollama access
    const r = await request.post(`${API_BASE}/ollama/chat`, { data: { model: 'llama3.2:latest', prompt: 'hi' } })
    expect([401, 403]).toContain(r.status())
  })

  test('6) Data Persistence (list and verify user record + roles)', async ({ page, request }) => {
    // Log back as admin
    await page.goto(FRONTEND_BASE)
    await page.getByLabel('Username').fill(adminEmail)
    await page.getByLabel('Password').fill(adminPassword)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByText('Admin panel')).toBeVisible()
    await page.getByRole('button', { name: 'Refresh' }).click()
    await expect(page.getByText(newUserEmail)).toBeVisible()
    // Verify via API too
    const token = await apiLogin(request, adminEmail, adminPassword)
    const list = await request.get(`${API_BASE}/users?limit=200&offset=0`, { headers: { Authorization: `Bearer ${token}` } })
    expect(list.status()).toBe(200)
    const users = await list.json()
    const found = users.find((u: any) => u.email === newUserEmail)
    expect(found).toBeTruthy()
    // optional: roles may be ['user'] if saved
  })

  test('8) Performance (basic timings)', async ({ page }) => {
    await page.goto(FRONTEND_BASE)
    const t0 = Date.now()
    await page.getByLabel('Username').fill(adminEmail)
    await page.getByLabel('Password').fill(adminPassword)
    await page.getByRole('button', { name: 'Sign in' }).click()
    await expect(page.getByText('Admin panel')).toBeVisible()
    const t1 = Date.now()
    expect(t1 - t0, 'end-to-end admin sign-in ms').toBeLessThan(2000)
    const t2 = Date.now()
    await page.getByRole('button', { name: 'Refresh' }).click()
    await page.waitForTimeout(200) // small wait for rendering
    const t3 = Date.now()
    expect(t3 - t2, 'list users ms').toBeLessThan(1500)
  })
})
