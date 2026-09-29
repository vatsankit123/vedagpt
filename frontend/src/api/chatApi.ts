import { apiFetch } from './client'
import { chatResponseSchema } from './schemas'
import { ApiError } from './errors'
import type { ChatRequest, ChatResponse } from './types'
export async function sendChatMessage(request: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  const raw = await apiFetch<unknown>('/api/v1/chat', { method: 'POST', body: JSON.stringify(request), signal })
  const parsed = chatResponseSchema.safeParse(raw)
  if (!parsed.success) throw new ApiError('malformed_response', 'The server returned an unexpected response format.')
  const { message, ...rest } = parsed.data
  return { ...rest, message: message ?? null }
}
