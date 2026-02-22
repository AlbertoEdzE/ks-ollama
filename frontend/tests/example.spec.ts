import { test, expect } from '@playwright/test'

test('loads app', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('User Management')).toBeVisible()
})
