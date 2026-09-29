import type { SourceCitation } from '@/api/types'
export type MessageRole = 'user' | 'assistant'
export type MessageStatus = 'pending' | 'success' | 'error' | 'cancelled'
export interface ChatMessage {
  id: string; role: MessageRole; content: string; createdAt: Date; status: MessageStatus;
  grounded?: boolean; sources?: SourceCitation[]; userMessage?: string;
  originalQuestion?: string; canRetry?: boolean;
}
