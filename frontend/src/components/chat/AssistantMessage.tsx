import { RefreshCw, AlertCircle, XCircle } from 'lucide-react'
import { GroundingBadge } from './GroundingBadge'
import { SourceList } from '@/components/sources/SourceList'
import type { ChatMessage } from '@/features/chat/chatTypes'
interface Props { message: ChatMessage; onRetry: () => void }
export function AssistantMessage({ message, onRetry }: Props) {
  if (message.status === 'error') return (
    <div className="flex items-start gap-3 animate-fade-in" role="alert">
      <AlertCircle className="h-5 w-5 text-red-400 mt-1 flex-shrink-0" aria-hidden="true" />
      <div className="card px-4 py-3 max-w-[85%] space-y-3">
        <p className="text-sm text-red-600 dark:text-red-400">{message.userMessage}</p>
        {message.canRetry && <button type="button" onClick={onRetry} className="btn-secondary text-xs"><RefreshCw className="h-3.5 w-3.5" aria-hidden="true" />Try again</button>}
      </div>
    </div>
  )
  if (message.status === 'cancelled') return (
    <div className="flex items-start gap-3 animate-fade-in">
      <XCircle className="h-5 w-5 text-stone-400 mt-1 flex-shrink-0" aria-hidden="true" />
      <div className="card px-4 py-3 max-w-[85%]"><p className="text-sm text-stone-500 dark:text-stone-400">Request cancelled.</p></div>
    </div>
  )
  return (
    <div className="flex items-start gap-3 animate-slide-up">
      <div className="flex-shrink-0 h-8 w-8 rounded-full bg-saffron-100 dark:bg-saffron-900 flex items-center justify-center text-saffron-600 dark:text-saffron-400 font-semibold text-xs select-none" aria-hidden="true">V</div>
      <div className="flex-1 max-w-[90%] space-y-3">
        <div className="card px-4 py-3"><p className="text-sm leading-relaxed text-stone-800 dark:text-stone-200 whitespace-pre-wrap">{message.content}</p></div>
        {message.status === 'success' && <GroundingBadge grounded={message.grounded??false} />}
        {message.grounded && message.sources && message.sources.length>0 && <SourceList sources={message.sources} />}
        {message.status==='success' && !message.grounded && message.content && <p className="text-xs text-stone-500 dark:text-stone-400">Consider rephrasing your question or asking about a specific verse.</p>}
      </div>
    </div>
  )
}
