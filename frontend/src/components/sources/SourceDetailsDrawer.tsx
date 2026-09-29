import { useEffect, useRef, type ReactNode } from 'react'
import { X } from 'lucide-react'
import type { SourceCitation } from '@/api/types'
import { formatVerseRef } from '@/lib/format'
import { env } from '@/config/env'
interface Props { source: SourceCitation | null; onClose: () => void }
export function SourceDetailsDrawer({ source, onClose }: Props) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const triggerRef = useRef<HTMLElement | null>(null)
  useEffect(() => {
    if (source) {
      triggerRef.current = document.activeElement as HTMLElement
      setTimeout(() => closeRef.current?.focus(), 50)
    } else if (triggerRef.current) {
      triggerRef.current.focus()
      triggerRef.current = null
    }
  }, [source])
  useEffect(() => {
    if (!source) return
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', h)
    return () => document.removeEventListener('keydown', h)
  }, [source, onClose])
  if (!source) return null
  const verseRef = formatVerseRef(source.chapter, source.verse)
  const dialogLabel = 'Source details: ' + source.scripture + ' ' + verseRef
  return (
    <>
      <div className="fixed inset-0 bg-black/30 dark:bg-black/50 z-40 backdrop-blur-sm" onClick={onClose} aria-hidden="true" />
      <div
        role="dialog"
        aria-modal="true"
        aria-label={dialogLabel}
        className="fixed inset-y-0 right-0 z-50 w-full sm:max-w-md bg-white dark:bg-stone-900 shadow-2xl overflow-y-auto flex flex-col animate-slide-up"
      >
        <div className="sticky top-0 bg-white dark:bg-stone-900 border-b border-stone-200 dark:border-stone-700 px-5 py-4 flex items-center justify-between">
          <div>
            <h2 className="font-semibold text-stone-900 dark:text-stone-50 text-base">{source.scripture} {verseRef}</h2>
            <p className="text-xs text-stone-400 dark:text-stone-500 mt-0.5">Source details</p>
          </div>
          <button ref={closeRef} type="button" onClick={onClose} aria-label="Close source details" className="btn-ghost p-2">
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
        <div className="flex-1 px-5 py-5 space-y-5">
          <Section title="Reference">
            <p className="text-sm text-stone-700 dark:text-stone-300">
              {source.scripture}, Chapter {source.chapter}, Verse {verseRef}
            </p>
          </Section>
          {source.translation && (
            <Section title="Translation">
              <p className="text-sm text-stone-700 dark:text-stone-300 leading-relaxed italic">
                &ldquo;{source.translation}&rdquo;
              </p>
            </Section>
          )}
          {source.translator && (
            <Section title="Translator">
              <p className="text-sm text-stone-600 dark:text-stone-400">{source.translator}</p>
            </Section>
          )}
          {source.edition && (
            <Section title="Edition">
              <p className="text-sm text-stone-600 dark:text-stone-400">{source.edition}</p>
            </Section>
          )}
          {source.source_reference && (
            <Section title="Source reference">
              <p className="text-sm text-stone-600 dark:text-stone-400 break-words">{source.source_reference}</p>
            </Section>
          )}
          {env.isDev && (
            <Section title="Development metadata">
              <dl className="text-xs font-mono space-y-1 text-stone-400">
                <div><dt className="inline">ID: </dt><dd className="inline">{source.document_id}</dd></div>
                <div><dt className="inline">Score: </dt><dd className="inline">{source.retrieval_score.toFixed(4)}</dd></div>
              </dl>
            </Section>
          )}
        </div>
        <footer className="px-5 py-4 border-t border-stone-200 dark:border-stone-700">
          <p className="text-xs text-stone-400 dark:text-stone-500">
            This translation was retrieved from the indexed corpus. Verify with authoritative editions.
          </p>
        </footer>
      </div>
    </>
  )
}
function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h3 className="text-xs font-semibold text-stone-400 dark:text-stone-500 uppercase tracking-wide mb-2">{title}</h3>
      {children}
    </section>
  )
}
