import { Spinner } from '@/components/common/Spinner'
export function ChatLoadingState() {
  return (
    <div className="flex items-start gap-3 animate-fade-in" role="status" aria-label="Generating answer...">
      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-saffron-100 dark:bg-saffron-900 flex items-center justify-center text-saffron-600 dark:text-saffron-400 font-semibold text-xs select-none" aria-hidden="true">V</div>
      <div className="card px-4 py-3 flex items-center gap-2">
        <Spinner size="sm" label="Generating answer..." />
        <span className="text-sm text-stone-500 dark:text-stone-400" aria-hidden="true">Retrieving relevant passages...</span>
      </div>
    </div>
  )
}
