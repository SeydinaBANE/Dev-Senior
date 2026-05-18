export type AgentType = 'dev-senior' | 'biz-manager'

const API_KEY = import.meta.env.VITE_API_KEY ?? ''
// VITE_API_URL allows deploying the frontend on a different host than the API.
// When empty (default), URLs are relative — works when FastAPI serves /app.
const API_BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

const headers = (): HeadersInit => ({
  'Content-Type': 'application/json',
  ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
})

export interface ChatResponse {
  response: string
  session_id: string
}

export type StreamChunk =
  | { type: 'session'; sessionId: string }
  | { type: 'chunk'; text: string }
  | { type: 'done' }

export async function* sendChatStream(
  agent: AgentType,
  message: string,
  sessionId: string,
): AsyncGenerator<StreamChunk> {
  const res = await fetch(`${API_BASE}/${agent}/chat/stream`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ message, session_id: sessionId }),
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  if (!res.body) throw new Error('No response body')

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      // SSE events are separated by double newlines
      const parts = buffer.split('\n\n')
      buffer = parts.pop() ?? ''

      for (const part of parts) {
        let eventType = 'message'
        let data = ''
        for (const line of part.split('\n')) {
          if (line.startsWith('event: ')) eventType = line.slice(7).trim()
          else if (line.startsWith('data: ')) data = line.slice(6)
        }
        if (!data) continue

        if (eventType === 'session') {
          yield { type: 'session', sessionId: data }
        } else if (eventType === 'error') {
          throw new Error(JSON.parse(data) as string)
        } else if (data === '[DONE]') {
          yield { type: 'done' }
          return
        } else {
          yield { type: 'chunk', text: JSON.parse(data) as string }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export async function resetSession(agent: AgentType, sessionId: string): Promise<void> {
  if (!sessionId) return
  await fetch(`${API_BASE}/${agent}/reset/${sessionId}`, {
    method: 'POST',
    headers: headers(),
  })
}
