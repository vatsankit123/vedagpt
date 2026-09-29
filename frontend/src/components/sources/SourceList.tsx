import { useState } from 'react'
import { SourceCard } from './SourceCard'
import { SourceDetailsDrawer } from './SourceDetailsDrawer'
import type { SourceCitation } from '@/api/types'
interface Props { sources: SourceCitation[] }
export function SourceList({ sources }: Props) {
  const [selected, setSelected] = useState<SourceCitation | null>(null)
  if (sources.length === 0) return null
  const countLabel = sources.length === 1 ? '1 indexed source' : sources.length + ' indexed sources'
  return (
    <div>
      <p className="text-xs font-medium text-stone-500 dark:text-stone-400 mb-2">{countLabel}</p>
      <ul className="space-y-2" role="list" aria-label="Source citations">
        {sources.map((s) => (
          <li key={s.document_id}>
            <SourceCard source={s} onOpen={() => setSelected(s)} />
          </li>
        ))}
      </ul>
      <SourceDetailsDrawer source={selected} onClose={() => setSelected(null)} />
    </div>
  )
}
