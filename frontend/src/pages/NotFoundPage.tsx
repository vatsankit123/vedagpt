import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { env } from '@/config/env'
export function NotFoundPage() {
  useEffect(() => { document.title = 'Page not found -- ' + env.appName }, [])
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center p-8 gap-4">
      <p className="text-6xl font-bold text-saffron-300 dark:text-saffron-700 select-none" aria-hidden="true">404</p>
      <h1 className="text-xl font-semibold text-stone-900 dark:text-stone-50">Page not found</h1>
      <p className="text-sm text-stone-500 dark:text-stone-400 max-w-xs">The page you are looking for does not exist.</p>
      <Link to="/" className="btn-primary">Go to chat</Link>
    </div>
  )
}
