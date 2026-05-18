import type { Message } from '../hooks/useChat'
import type { AgentType } from '../api/agents'

interface Props {
  message: Message
  agent: AgentType
}

export function MessageBubble({ message, agent }: Props) {
  const isUser = message.role === 'user'
  const accentClass = agent === 'dev-senior' ? 'bg-dev-700' : 'bg-biz-700'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-3`}>
      {!isUser && (
        <div className={`w-7 h-7 rounded-full ${accentClass} flex items-center justify-center text-xs mr-2 mt-1 shrink-0`}>
          {agent === 'dev-senior' ? '💻' : '📊'}
        </div>
      )}
      <div
        className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-gray-700 text-gray-100 rounded-br-sm'
            : 'bg-gray-800 text-gray-100 rounded-bl-sm'
        }`}
      >
        {message.attachment && (
          <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-2 pb-2 border-b border-gray-600">
            <span>📎</span>
            <span className="truncate max-w-[200px]">{message.attachment}</span>
          </div>
        )}
        {message.content}
        {message.streaming && (
          <span className="inline-block w-0.5 h-4 ml-0.5 bg-gray-400 align-middle animate-pulse" />
        )}
        {!message.streaming && (
          <div className="text-xs text-gray-500 mt-1">
            {message.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
          </div>
        )}
      </div>
      {isUser && (
        <div className="w-7 h-7 rounded-full bg-gray-600 flex items-center justify-center text-xs ml-2 mt-1 shrink-0">
          👤
        </div>
      )}
    </div>
  )
}
