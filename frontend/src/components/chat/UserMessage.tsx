import type { ChatMessage } from '@/features/chat/chatTypes'
import { formatRelativeTime } from '@/lib/format'
interface Props { message: ChatMessage }
export function UserMessage({ message }: Props) {
  return (
    <div className="flex justify-end animate-fade-in">
      <div className="max-w-[80%]">
        <div className="bg-indigo-600 dark:bg-indigo-700 text-white rounded-2xl rounded-tr-sm px-4 py-3 text-sm leading-relaxed">{message.content}</div>
        <p className="text-right text-xs text-stone-400 dark:text-stone-500 mt-1 mr-1"><time dateTime={message.createdAt.toISOString()}>{formatRelativeTime(message.createdAt)}</time></p>
      </div>
    </div>
  )
}
