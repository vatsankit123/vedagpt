import { useState, useCallback, useRef } from 'react'
import { sendChatMessage } from '@/api/chatApi'
import { ApiError, userFacingMessage } from '@/api/errors'
import { loadHistory, saveHistory, clearHistory } from './chatState'
import type { ChatMessage } from './chatTypes'
let _counter = 0
function nextId(): string { return 'msg-' + Date.now() + '-' + (++_counter) }
export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>(loadHistory)
  const [isLoading, setIsLoading] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const update = useCallback((next: ChatMessage[]) => { setMessages(next); saveHistory(next) }, [])
  const sendMessage = useCallback(async (question: string) => {
    const trimmed = question.trim()
    if (!trimmed || isLoading) return
    const userMsg: ChatMessage = { id: nextId(), role: 'user', content: trimmed, createdAt: new Date(), status: 'success' }
    const aid = nextId()
    const pending: ChatMessage = { id: aid, role: 'assistant', content: '', createdAt: new Date(), status: 'pending', originalQuestion: trimmed }
    const base = [...messages, userMsg, pending]
    update(base)
    setIsLoading(true)
    const ctrl = new AbortController()
    abortRef.current = ctrl
    try {
      const resp = await sendChatMessage({ question: trimmed, top_k: 5 }, ctrl.signal)
      const done: ChatMessage = { id: aid, role: 'assistant', content: resp.answer, createdAt: new Date(), status: 'success', grounded: resp.grounded, sources: resp.sources, originalQuestion: trimmed }
      update([...base.filter((m) => m.id !== aid), done])
    } catch (err) {
      const cancelled = err instanceof ApiError && err.kind === 'cancelled'
      const errMsg: ChatMessage = { id: aid, role: 'assistant', content: '', createdAt: new Date(), status: cancelled ? 'cancelled' : 'error', userMessage: userFacingMessage(err), originalQuestion: trimmed, canRetry: !cancelled }
      update([...base.filter((m) => m.id !== aid), errMsg])
    } finally { setIsLoading(false); abortRef.current = null }
  }, [messages, isLoading, update])
  const cancelRequest = useCallback(() => { abortRef.current?.abort() }, [])
  const retryMessage = useCallback((q: string) => { sendMessage(q) }, [sendMessage])
  const clearConversation = useCallback(() => { setMessages([]); clearHistory() }, [])
  return { messages, isLoading, sendMessage, cancelRequest, retryMessage, clearConversation }
}
