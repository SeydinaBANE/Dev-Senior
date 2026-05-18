import { useState, useCallback, useRef, useEffect } from 'react'
import { sendChatStream, resetSession, type AgentType } from '../api/agents'

export interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: Date
  streaming?: boolean  // true tant que le stream n'est pas terminé
}

export function useChat(agent: AgentType) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)   // true = attente du 1er token
  const [streaming, setStreaming] = useState(false) // true = tokens en cours
  const [error, setError] = useState<string | null>(null)
  const sessionId = useRef<string>('')

  useEffect(() => {
    setMessages([])
    setError(null)
    sessionId.current = ''
  }, [agent])

  const send = useCallback(async (text: string) => {
    if (!text.trim() || loading || streaming) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    setError(null)

    const agentMsgId = crypto.randomUUID()

    try {
      for await (const chunk of sendChatStream(agent, text, sessionId.current)) {
        if (chunk.type === 'session') {
          sessionId.current = chunk.sessionId
        } else if (chunk.type === 'chunk') {
          if (loading) {
            // Premier token : quitter le mode "attente" et afficher la bulle
            setLoading(false)
            setStreaming(true)
            setMessages(prev => [
              ...prev,
              { id: agentMsgId, role: 'agent', content: chunk.text, timestamp: new Date(), streaming: true },
            ])
          } else {
            // Tokens suivants : accumuler dans la bulle existante
            setMessages(prev =>
              prev.map(m =>
                m.id === agentMsgId ? { ...m, content: m.content + chunk.text } : m,
              ),
            )
          }
        } else if (chunk.type === 'done') {
          setMessages(prev =>
            prev.map(m => (m.id === agentMsgId ? { ...m, streaming: false } : m)),
          )
          setStreaming(false)
        }
      }
    } catch (e) {
      setMessages(prev => prev.filter(m => m.id !== agentMsgId))
      setError(e instanceof Error ? e.message : 'Erreur inattendue')
      setLoading(false)
      setStreaming(false)
    }
  }, [agent, loading, streaming])

  const reset = useCallback(async () => {
    await resetSession(agent, sessionId.current)
    sessionId.current = ''
    setMessages([])
    setError(null)
  }, [agent])

  return { messages, loading, streaming, error, send, reset }
}
