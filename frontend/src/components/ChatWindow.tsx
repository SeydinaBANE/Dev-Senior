import { useEffect, useRef } from 'react'
import type { Message } from '../hooks/useChat'
import type { AgentType } from '../api/agents'
import { MessageBubble } from './MessageBubble'

interface Props {
  agent: AgentType
  messages: Message[]
  loading: boolean    // attente du 1er token
  streaming: boolean  // tokens en cours (bulle visible)
  error: string | null
}

const WELCOME: Record<AgentType, { title: string; subtitle: string }> = {
  'dev-senior': {
    title: 'Agent Dev Senior',
    subtitle: 'Posez une question technique, demandez une code review, une analyse d\'architecture…',
  },
  'biz-manager': {
    title: 'Agent Business Manager',
    subtitle: 'Stratégie marketing, analyse SEO, rédaction de contenus, gestion CRM…',
  },
}

export function ChatWindow({ agent, messages, loading, streaming, error }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading, streaming])

  const { title, subtitle } = WELCOME[agent]

  return (
    <main className="flex-1 overflow-y-auto scrollbar-thin p-6">
      {messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-center opacity-60">
          <div className="text-5xl mb-4">{agent === 'dev-senior' ? '💻' : '📊'}</div>
          <h2 className="text-xl font-semibold text-gray-300 mb-2">{title}</h2>
          <p className="text-sm text-gray-500 max-w-sm">{subtitle}</p>
        </div>
      )}

      {messages.map(m => (
        <MessageBubble key={m.id} message={m} agent={agent} />
      ))}

      {/* Dots "thinking" : uniquement pendant l'attente du 1er token */}
      {loading && !streaming && (
        <div className="flex justify-start mb-3">
          <div className="bg-gray-800 rounded-2xl rounded-bl-sm px-4 py-3">
            <span className="inline-flex gap-1">
              {[0, 1, 2].map(i => (
                <span
                  key={i}
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </span>
          </div>
        </div>
      )}

      {error && (
        <div className="flex justify-center mb-3">
          <div className="bg-red-900/50 text-red-300 text-sm rounded-xl px-4 py-2 border border-red-800">
            ⚠ {error}
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </main>
  )
}
