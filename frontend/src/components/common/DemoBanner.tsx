import { AlertTriangle } from 'lucide-react'
export function DemoBanner() {
  return (
    <div role="alert" aria-label="Demo data notice" className="bg-amber-50 dark:bg-amber-950 border-b border-amber-200 dark:border-amber-800 px-4 py-2">
      <div className="max-w-5xl mx-auto flex items-start gap-2 text-xs text-amber-800 dark:text-amber-300">
        <AlertTriangle className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" aria-hidden="true" />
        <p>
          <strong>Demonstration mode:</strong> VedaGPT is running with limited test data.
          Responses and citations are for technical evaluation and should <strong>not</strong> be treated as authoritative scripture references.
        </p>
      </div>
    </div>
  )
}
