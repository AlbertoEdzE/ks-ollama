import { render } from '@testing-library/react'
import '@testing-library/jest-dom'
import { axe } from 'jest-axe'
import App from './App'

it('has no a11y violations', async () => {
  const { container } = render(<App />)
  const results = await axe(container)
  expect(results.violations).toHaveLength(0)
})
