import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import { env } from '@/config/env'
interface Props { children?: ReactNode }
interface State { hasError: boolean; devMessage?: string }
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }
  static getDerivedStateFromError(e: Error): State { return { hasError: true, devMessage: env.isDev ? e.message : undefined } }
  componentDidCatch(e: Error, i: ErrorInfo) { if (env.isDev) console.error('[ErrorBoundary]', e, i) }
  render() {
    if (this.state.hasError) return (
      <div className="flex flex-col items-center justify-center min-h-[40vh] p-8 text-center gap-4">
        <AlertTriangle className="h-10 w-10 text-amber-500" aria-hidden="true" />
        <h2 className="text-lg font-semibold text-stone-900 dark:text-stone-50">Something went wrong</h2>
        <p className="text-sm text-stone-500 dark:text-stone-400 max-w-sm">An unexpected error occurred. Please reload the page to continue.</p>
        {env.isDev && this.state.devMessage && <p className="text-xs font-mono text-red-500 bg-red-50 px-3 py-2 rounded-lg max-w-sm break-all">{this.state.devMessage}</p>}
        <button type="button" onClick={() => window.location.reload()} className="btn-primary">Reload page</button>
      </div>
    )
    return this.props.children
  }
}
