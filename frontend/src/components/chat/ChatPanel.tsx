import { useEffect, useRef } from 'react'
import { Trash2 } from 'lucide-react'
import { useChat } from '@/features/chat/useChat'
import { ChatComposer } from './ChatComposer'
import { ChatMessage } from './ChatMessage'
import { ChatEmptyState } from './ChatEmptyState'
import { ChatLoadingState } from './ChatLoadingState'
export function ChatPanel() {
  const { messages, isLoading, sendMessage, cancelRequest, retryMessage, clearConversation } = useChat()
  const bottomRef = useRef<HTMLDivElement>(null)
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages.length])
  const hasMessages = messages.length > 0
  return (
    <div className="flex flex-col h-full max-w-3xl mx-auto w-full px-4 sm:px-6">
      {hasMessages && (
        <div className="flex justify-end pt-3 pb-1">
          <button type="button" onClick={clearConversation} className="btn-ghost text-xs gap-1.5" aria-label="Clear conversation">
            <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />Clear
          </button>
        </div>
      )}
      <div role="log" aria-label="Conversation" aria-live="polite" className="flex-1 overflow-y-auto py-4 space-y-4 min-h-0">
        {!hasMessages && !isLoading && <ChatEmptyState onSelectQuestion={sendMessage} />}
        {messages.map((m) => (
          <ChatMessage key={m.id} message={m} onRetry={() => m.originalQuestion && retryMessage(m.originalQuestion)} />
        ))}
        {isLoading && messages[messages.length-1]?.status==='pending' && <ChatLoadingState />}
        <div ref={bottomRef} aria-hidden="true" />
      </div>
      <div className="sticky bottom-0 pb-4 pt-2 bg-stone-50 dark:bg-stone-950">
        <ChatComposer onSend={sendMessage} onCancel={cancelRequest} isLoading={isLoading} />
      </div>
    </div>
  )
}
