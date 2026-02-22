import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import App from './App'

it('renders heading and login form', () => {
  render(<App />)
  expect(screen.getByText(/User Management/)).toBeInTheDocument()
  expect(screen.getByText(/Admin login/)).toBeInTheDocument()
  expect(screen.getByLabelText(/Username/)).toBeInTheDocument()
  expect(screen.getByLabelText(/Password/)).toBeInTheDocument()
})

it('shows validation message when login fields are empty', async () => {
  render(<App />)
  const button = screen.getByRole('button', { name: /Sign in/ })
  fireEvent.click(button)
  await waitFor(() => {
    expect(screen.getByRole('alert')).toHaveTextContent(/Username and password are required/)
  })
})*** End Patch
