import { ExternalLink } from 'lucide-react'
import type { SourceCitation } from '@/api/types'
import { formatVerseRef, truncate } from '@/lib/format'
import { env } from '@/config/env'
interface Props { source: SourceCitation; onOpen: () => void }
export function SourceCard({ source, onOpen }: Props) {
  const verseRef = formatVerseRef(source.chapter, source.verse)
  const label = source.scripture + ' ' + verseRef
  return (
    <article className="card px-3 py-2.5 hover:border-saffron-300 dark:hover:border-saffron-700 transition-colors">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <h3 className="text-xs font-semibold text-stone-700 dark:text-stone-300 truncate">{label}</h3>
          {source.translation && (
            <p className="text-xs text-stone-600 dark:text-stone-400 mt-1 line-clamp-2">
              {truncate(source.translation, 160)}
            </p>
          )}
          <div className="flex flex-wrap gap-2 mt-1.5">
            {source.translator && (
              <span className="text-xs text-stone-400 dark:text-stone-500">Trans: {source.translator}</span>
            )}
            {source.edition && (
              <span className="text-xs text-stone-400 dark:text-stone-500">{source.edition}</span>
            )}
            {env.isDev && (
              <span className="text-xs text-stone-300 dark:text-stone-600 font-mono">
                score: {source.retrieval_score.toFixed(3)}
              </span>
            )}
          </div>
        </div>
        <button
          type="button"
          onClick={onOpen}
          aria-label={'View details for ' + label}
          className="flex-shrink-0 btn-ghost p-1.5"
        >
          <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
        </button>
      </div>
    </article>
  )
}
