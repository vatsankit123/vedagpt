import { Suspense } from 'react'
import { Outlet } from 'react-router-dom'
import { AppHeader } from './AppHeader'
import { Spinner } from '@/components/common/Spinner'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import { DemoBanner } from '@/components/common/DemoBanner'
import { env } from '@/config/env'
export function AppShell() {
  return (
    <div className="flex flex-col min-h-screen bg-stone-50 dark:bg-stone-950">
      <AppHeader />
      {env.isDemoMode && <DemoBanner />}
      <main id="main-content" className="flex-1 flex flex-col" tabIndex={-1}>
        <ErrorBoundary>
          <Suspense fallback={<div className="flex-1 flex items-center justify-center"><Spinner size="lg" label="Loading page..." /></div>}>
            <Outlet />
          </Suspense>
        </ErrorBoundary>
      </main>
      <div role="status" aria-live="polite" aria-atomic="true" className="sr-only" id="live-region" />
    </div>
  )
}
