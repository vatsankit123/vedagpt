import { useState, useRef, type KeyboardEvent, type FormEvent } from 'react'
import { Send, X } from 'lucide-react'
import { cn } from '@/lib/cn'
const MAX_LENGTH = 1000
const COUNTER_THRESHOLD = 800
interface Props { onSend: (q: string) => void; onCancel: () => void; isLoading: boolean }
export function ChatComposer({ onSend, onCancel, isLoading }: Props) {
  const [draft, setDraft] = useState('')
  const ref = useRef<HTMLTextAreaElement>(null)
  const isBlank = draft.trim().length === 0
  const remaining = MAX_LENGTH - draft.length
  function submit() { const t = draft.trim(); if (!t || isLoading) return; onSend(t); setDraft(''); ref.current?.focus() }
  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) { if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); submit() } }
  return (
    <form onSubmit={(e: FormEvent) => { e.preventDefault(); submit() }} className="card p-3" aria-label="Chat composer" noValidate>
      <div className="flex items-end gap-2">
        <div className="flex-1 relative">
          <label htmlFor="chat-input" className="sr-only">Ask a question about the indexed scripture</label>
          <textarea
            id="chat-input" ref={ref} value={draft}
            onChange={(e) => setDraft(e.target.value.slice(0, MAX_LENGTH))}
            onKeyDown={handleKeyDown}
            placeholder="Ask about duty, karma, the mind, or a specific verse..."
            rows={1} disabled={isLoading} maxLength={MAX_LENGTH}
            aria-label="Your question"
            aria-describedby={remaining<=COUNTER_THRESHOLD?'char-count':undefined}
            className={cn('input-base resize-none min-h-[44px] max-h-40 overflow-y-auto py-2.5')}
          />
          {remaining<=COUNTER_THRESHOLD && (
            <p id="char-count" className={cn('absolute bottom-2 right-2 text-xs tabular-nums', remaining<100?'text-red-500':'text-stone-400')} aria-live="polite">{remaining}</p>
          )}
        </div>
        {isLoading ? (
          <button type="button" onClick={onCancel} aria-label="Cancel request" className="btn-secondary p-2.5 h-[44px] w-[44px] flex items-center justify-center flex-shrink-0"><X className="h-4 w-4" aria-hidden="true" /></button>
        ) : (
          <button type="submit" disabled={isBlank} aria-label="Send message" className="btn-primary p-2.5 h-[44px] w-[44px] flex items-center justify-center flex-shrink-0"><Send className="h-4 w-4" aria-hidden="true" /></button>
        )}
      </div>
      <p className="text-xs text-stone-400 dark:text-stone-500 mt-2 px-1">Press <kbd className="font-mono">Enter</kbd> to send, <kbd className="font-mono">Shift+Enter</kbd> for new line</p>
    </form>
  )
}
