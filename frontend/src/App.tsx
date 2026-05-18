import { useState } from 'react'
import type { AgentType } from './api/agents'
import { Sidebar } from './components/Sidebar'
import type { ViewType } from './components/Sidebar'
import { ChatWindow } from './components/ChatWindow'
import { InputBar } from './components/InputBar'
import { MetricsDashboard } from './components/MetricsDashboard'
import { useChat } from './hooks/useChat'

export default function App() {
  const [view, setView] = useState<ViewType>('dev-senior')
  const agent: AgentType = view === 'dashboard' ? 'dev-senior' : view
  const { messages, loading, streaming, error, send, reset } = useChat(agent)
  const busy = loading || streaming

  return (
    <div className="flex h-full">
      <Sidebar active={view} onChange={setView} />
      {view === 'dashboard' ? (
        <MetricsDashboard />
      ) : (
        <div className="flex-1 flex flex-col min-h-0">
          <ChatWindow agent={agent} messages={messages} loading={loading} streaming={streaming} error={error} />
          <InputBar agent={agent} loading={busy} onSend={send} onReset={reset} />
        </div>
      )}
    </div>
  )
}
