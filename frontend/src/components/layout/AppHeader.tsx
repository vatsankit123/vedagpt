import { Link, NavLink } from 'react-router-dom'
import { BookOpen } from 'lucide-react'
import { ThemeToggle } from '@/components/common/ThemeToggle'
import { HealthIndicator } from '@/components/common/HealthIndicator'
import { env } from '@/config/env'
export function AppHeader() {
  return (
    <header className="sticky top-0 z-40 bg-white/90 dark:bg-stone-950/90 backdrop-blur border-b border-stone-200 dark:border-stone-800">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-4">
        <Link to="/" className="flex items-center gap-2 text-stone-900 dark:text-stone-50 hover:opacity-80 transition-opacity focus-ring rounded" aria-label="VedaGPT home">
          <BookOpen className="h-5 w-5 text-saffron-500" aria-hidden="true" />
          <span className="font-semibold text-base tracking-tight">{env.appName}</span>
        </Link>
        <span className="hidden sm:block text-xs text-stone-400 dark:text-stone-500 select-none">
          Source-grounded scripture learning
        </span>
        <div className="ml-auto flex items-center gap-2">
          <nav aria-label="Primary navigation">
            <ul className="flex items-center gap-1" role="list">
              <li>
                <NavLink to="/" end className={({ isActive }: { isActive: boolean }) => isActive ? 'btn-ghost text-xs text-saffron-600 dark:text-saffron-400' : 'btn-ghost text-xs'}>
                  Chat
                </NavLink>
              </li>
              <li>
                <NavLink to="/about" className={({ isActive }: { isActive: boolean }) => isActive ? 'btn-ghost text-xs text-saffron-600 dark:text-saffron-400' : 'btn-ghost text-xs'}>
                  About
                </NavLink>
              </li>
            </ul>
          </nav>
          <HealthIndicator />
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
