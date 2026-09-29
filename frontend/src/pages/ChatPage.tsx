import { useEffect } from 'react'
import { ChatPanel } from '@/components/chat/ChatPanel'
import { env } from '@/config/env'
export function ChatPage() {
  useEffect(() => { document.title = env.appName + ' -- Scripture learning' }, [])
  return <div className="flex-1 flex flex-col" style={{ minHeight: 0 }}><ChatPanel /></div>
}
