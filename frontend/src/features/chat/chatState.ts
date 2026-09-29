import { env } from '@/config/env'
import type { ChatMessage } from './chatTypes'
import type { SourceCitation } from '@/api/types'

const STORAGE_KEY = 'vedagpt-chat-v1'
const MAX_HISTORY = 50

interface StoredMessage {
  id: string; role: string; content: string; createdAt: string;
  status: string; grounded?: boolean; sources?: unknown[];
}

function isSourceCitation(v: unknown): v is SourceCitation {
  if (typeof v !== 'object' || v === null) return false
  const o = v as Record<string, unknown>
  return typeof o.document_id === 'string' && typeof o.scripture === 'string' && typeof o.chapter === 'number' && typeof o.verse === 'number' && typeof o.retrieval_score === 'number'
}

function isStoredMessage(v: unknown): v is StoredMessage {
  if (typeof v !== 'object' || v === null) return false
  const o = v as Record<string, unknown>
  return typeof o.id === 'string' && (o.role === 'user' || o.role === 'assistant') && typeof o.content === 'string'
}

export function loadHistory(): ChatMessage[] {
  if (!env.enableLocalHistory) return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return (parsed as unknown[]).filter(isStoredMessage).map((m): ChatMessage => ({
      id: m.id,
      role: m.role as 'user' | 'assistant',
      content: m.content,
      createdAt: new Date(m.createdAt),
      status: (m.status as ChatMessage['status']) ?? 'success',
      grounded: m.grounded,
      sources: Array.isArray(m.sources) ? m.sources.filter(isSourceCitation) : [],
    })).slice(-MAX_HISTORY)
  } catch { return [] }
}

export function saveHistory(messages: ChatMessage[]): void {
  if (!env.enableLocalHistory) return
  try {
    const safe: StoredMessage[] = messages.slice(-MAX_HISTORY).map((m) => ({
      id: m.id, role: m.role, content: m.content,
      createdAt: m.createdAt.toISOString(),
      status: m.status, grounded: m.grounded, sources: m.sources ?? [],
    }))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(safe))
  } catch { /* localStorage full */ }
}

export function clearHistory(): void { try { localStorage.removeItem(STORAGE_KEY) } catch { /* ignore */ } }
