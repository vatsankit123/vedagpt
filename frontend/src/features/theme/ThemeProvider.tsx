import { useEffect, useState, type ReactNode } from 'react'
import { ThemeContext } from './ThemeContext'
import { getSystemTheme } from './systemTheme'
import type { Theme } from './ThemeContext'

const STORAGE_KEY = 'vedagpt-theme'

function loadStoredTheme(): Theme {
  try {
    const s = localStorage.getItem(STORAGE_KEY)
    if (s === 'light' || s === 'dark' || s === 'system') return s
  } catch {
    // localStorage unavailable
  }
  return 'system'
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(loadStoredTheme)
  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>(
    () => (theme === 'system' ? getSystemTheme() : theme)
  )

  useEffect(() => {
    const r = theme === 'system' ? getSystemTheme() : theme
    setResolvedTheme(r)
    document.documentElement.classList.remove('light', 'dark')
    document.documentElement.classList.add(r)
  }, [theme])

  useEffect(() => {
    if (theme !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const h = () => {
      const r = getSystemTheme()
      setResolvedTheme(r)
      document.documentElement.classList.remove('light', 'dark')
      document.documentElement.classList.add(r)
    }
    mq.addEventListener('change', h)
    return () => mq.removeEventListener('change', h)
  }, [theme])

  function setTheme(next: Theme) {
    setThemeState(next)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // localStorage unavailable
    }
  }

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
