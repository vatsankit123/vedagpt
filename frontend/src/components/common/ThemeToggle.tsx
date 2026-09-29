import { Sun, Moon } from 'lucide-react'
import { useTheme } from '@/features/theme/useTheme'
export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme()
  function toggle() { setTheme(resolvedTheme === 'dark' ? 'light' : 'dark') }
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={resolvedTheme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
      className="btn-ghost p-2"
    >
      {resolvedTheme === 'dark' ? (
        <Sun className="h-4 w-4" aria-hidden="true" />
      ) : (
        <Moon className="h-4 w-4" aria-hidden="true" />
      )}
    </button>
  )
}
