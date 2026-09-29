import { UserMessage } from './UserMessage'
import { AssistantMessage } from './AssistantMessage'
import type { ChatMessage as T } from '@/features/chat/chatTypes'
interface Props { message: T; onRetry: () => void }
export function ChatMessage({ message, onRetry }: Props) {
  if (message.role === 'user') return <UserMessage message={message} />
  return <AssistantMessage message={message} onRetry={onRetry} />
}
