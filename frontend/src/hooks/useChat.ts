import { useState, useCallback, useRef, useEffect } from 'react'
import { sendChat, resetSession, type AgentType } from '../api/agents'

export interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: Date
}

export function useChat(agent: AgentType) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const sessionId = useRef<string>('')

  // Reset when agent switches
  useEffect(() => {
    setMessages([])
    setError(null)
    sessionId.current = ''
  }, [agent])

  const send = useCallback(async (text: string) => {
    if (!text.trim() || loading) return

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    setError(null)

    try {
      const res = await sendChat(agent, text, sessionId.current)
      sessionId.current = res.session_id
      const agentMsg: Message = {
        id: crypto.randomUUID(),
        role: 'agent',
        content: res.response,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, agentMsg])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur inattendue')
    } finally {
      setLoading(false)
    }
  }, [agent, loading])

  const reset = useCallback(async () => {
    await resetSession(agent, sessionId.current)
    sessionId.current = ''
    setMessages([])
    setError(null)
  }, [agent])

  return { messages, loading, error, send, reset }
}
