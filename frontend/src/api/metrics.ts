const API_KEY = import.meta.env.VITE_API_KEY ?? ''

export interface AgentMetrics {
  requests_total: number
  errors_total: number
  error_rate: number
  latency_p50_ms: number
  latency_p95_ms: number
}

export interface EvalScores {
  score?: number
  helpfulness?: number
  accuracy?: number
  safety?: number
}

export interface MetricsResponse {
  agents: Record<string, AgentMetrics>
  eval: Record<string, EvalScores>
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  const res = await fetch('/metrics', {
    headers: API_KEY ? { 'X-API-Key': API_KEY } : {},
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
