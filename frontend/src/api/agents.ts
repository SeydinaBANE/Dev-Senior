export type AgentType = 'dev-senior' | 'biz-manager'

const API_KEY = import.meta.env.VITE_API_KEY ?? ''

const headers = (): HeadersInit => ({
  'Content-Type': 'application/json',
  ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
})

export interface ChatResponse {
  response: string
  session_id: string
}

export async function sendChat(
  agent: AgentType,
  message: string,
  sessionId: string
): Promise<ChatResponse> {
  const res = await fetch(`/${agent}/chat`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ message, session_id: sessionId }),
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function resetSession(agent: AgentType, sessionId: string): Promise<void> {
  if (!sessionId) return
  await fetch(`/${agent}/reset/${sessionId}`, {
    method: 'POST',
    headers: headers(),
  })
}
