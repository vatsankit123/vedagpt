import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider } from '../ThemeProvider'
import { useTheme } from '../useTheme'

function Reader() {
  const { resolvedTheme, setTheme } = useTheme()
  return (
    <div>
      <span data-testid="t">{resolvedTheme}</span>
      <button onClick={() => setTheme('dark')}>Dark</button>
      <button onClick={() => setTheme('light')}>Light</button>
    </div>
  )
}

describe('ThemeProvider', () => {
  beforeEach(() => { localStorage.clear(); document.documentElement.classList.remove('light','dark') })

  it('provides a resolved theme', () => {
    render(<ThemeProvider><Reader /></ThemeProvider>)
    expect(['light','dark']).toContain(screen.getByTestId('t').textContent)
  })

  it('switches to dark', () => {
    render(<ThemeProvider><Reader /></ThemeProvider>)
    fireEvent.click(screen.getByText('Dark'))
    expect(screen.getByTestId('t').textContent).toBe('dark')
  })

  it('persists theme to localStorage', () => {
    render(<ThemeProvider><Reader /></ThemeProvider>)
    fireEvent.click(screen.getByText('Light'))
    expect(localStorage.getItem('vedagpt-theme')).toBe('light')
  })

  it('handles invalid stored theme safely', () => {
    localStorage.setItem('vedagpt-theme', 'invalid')
    expect(() => render(<ThemeProvider><Reader /></ThemeProvider>)).not.toThrow()
  })
})
