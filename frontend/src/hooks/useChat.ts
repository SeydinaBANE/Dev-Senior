import { useState, useCallback, useRef, useEffect } from 'react'
import { sendChatStream, uploadFile, resetSession, type AgentType } from '../api/agents'

export interface Message {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: Date
  streaming?: boolean
  attachment?: string  // filename du fichier joint, pour affichage
}

export interface PendingDoc {
  filename: string
  text: string
}

export function useChat(agent: AgentType) {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pendingDoc, setPendingDoc] = useState<PendingDoc | null>(null)
  const sessionId = useRef<string>('')

  useEffect(() => {
    setMessages([])
    setError(null)
    setPendingDoc(null)
    sessionId.current = ''
  }, [agent])

  const attachFile = useCallback(async (file: File) => {
    setUploading(true)
    setError(null)
    try {
      const result = await uploadFile(agent, file)
      setPendingDoc({ filename: result.filename, text: result.text })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur lors du chargement du fichier')
    } finally {
      setUploading(false)
    }
  }, [agent])

  const detachFile = useCallback(() => {
    setPendingDoc(null)
  }, [])

  const send = useCallback(async (text: string) => {
    if (!text.trim() || loading || streaming) return

    // Capture + clear before the async chain to avoid stale closure issues
    const docSnapshot = pendingDoc
    setPendingDoc(null)

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
      attachment: docSnapshot?.filename,
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    setError(null)

    const agentMsgId = crypto.randomUUID()

    try {
      for await (const chunk of sendChatStream(agent, text, sessionId.current, docSnapshot?.text ?? '')) {
        if (chunk.type === 'session') {
          sessionId.current = chunk.sessionId
        } else if (chunk.type === 'chunk') {
          if (loading) {
            setLoading(false)
            setStreaming(true)
            setMessages(prev => [
              ...prev,
              { id: agentMsgId, role: 'agent', content: chunk.text, timestamp: new Date(), streaming: true },
            ])
          } else {
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
  }, [agent, loading, streaming, pendingDoc])

  const reset = useCallback(async () => {
    await resetSession(agent, sessionId.current)
    sessionId.current = ''
    setMessages([])
    setError(null)
    setPendingDoc(null)
  }, [agent])

  return { messages, loading, streaming, uploading, error, pendingDoc, send, reset, attachFile, detachFile }
}
