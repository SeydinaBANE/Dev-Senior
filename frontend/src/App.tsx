import { useState } from 'react'
import type { AgentType } from './api/agents'
import { Sidebar } from './components/Sidebar'
import { ChatWindow } from './components/ChatWindow'
import { InputBar } from './components/InputBar'
import { useChat } from './hooks/useChat'

export default function App() {
  const [agent, setAgent] = useState<AgentType>('dev-senior')
  const { messages, loading, error, send, reset } = useChat(agent)

  return (
    <div className="flex h-full">
      <Sidebar active={agent} onChange={setAgent} />
      <div className="flex-1 flex flex-col min-h-0">
        <ChatWindow agent={agent} messages={messages} loading={loading} error={error} />
        <InputBar agent={agent} loading={loading} onSend={send} onReset={reset} />
      </div>
    </div>
  )
}
