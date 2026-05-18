import { useEffect, useState, useCallback } from 'react'
import { fetchMetrics } from '../api/metrics'
import type { MetricsResponse } from '../api/metrics'

const AGENTS = [
  { id: 'dev-senior', label: 'Dev Senior', color: 'dev' },
  { id: 'biz-manager', label: 'Business Manager', color: 'biz' },
]

function StatCard({ label, value, unit = '', sub }: { label: string; value: string | number; unit?: string; sub?: string }) {
  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">{label}</p>
      <p className="text-2xl font-bold text-white">
        {value}<span className="text-sm font-normal text-gray-400 ml-1">{unit}</span>
      </p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round((value / 5) * 100)
  const color = value >= 4 ? 'bg-green-500' : value >= 3 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-400 mb-1">
        <span>{label}</span>
        <span className="font-medium text-white">{value.toFixed(1)}/5</span>
      </div>
      <div className="h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function AgentCard({ label, color, data, eval: evalScores }: {
  label: string; color: string
  data: MetricsResponse['agents'][string] | undefined
  eval: MetricsResponse['eval'][string] | undefined
}) {
  const accent = color === 'dev' ? 'border-dev-500' : 'border-biz-500'
  const tag = color === 'dev' ? 'bg-dev-900 text-dev-300' : 'bg-biz-900 text-biz-300'

  return (
    <div className={`bg-gray-900 border ${accent} rounded-2xl p-6 space-y-6`}>
      <div className="flex items-center gap-3">
        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${tag}`}>{label}</span>
      </div>

      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wide mb-3">Trafic</p>
        <div className="grid grid-cols-2 gap-3">
          <StatCard label="Requêtes" value={data?.requests_total ?? 0} />
          <StatCard
            label="Taux d'erreur"
            value={data ? `${(data.error_rate * 100).toFixed(1)}` : '—'}
            unit="%"
            sub={`${data?.errors_total ?? 0} erreurs`}
          />
          <StatCard label="Latence P50" value={data?.latency_p50_ms ?? '—'} unit="ms" />
          <StatCard label="Latence P95" value={data?.latency_p95_ms ?? '—'} unit="ms" />
        </div>
      </div>

      {evalScores && Object.keys(evalScores).length > 0 && (
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-3">Qualité (dernier eval)</p>
          <div className="space-y-3">
            {(['score', 'helpfulness', 'accuracy', 'safety'] as const).map(k =>
              evalScores[k] !== undefined ? (
                <ScoreBar key={k} label={k} value={evalScores[k]!} />
              ) : null
            )}
          </div>
        </div>
      )}

      {(!evalScores || Object.keys(evalScores).length === 0) && (
        <p className="text-xs text-gray-600 italic">Aucun score d'éval — lance `make run-eval-cron`</p>
      )}
    </div>
  )
}

export function MetricsDashboard() {
  const [data, setData] = useState<MetricsResponse | null>(null)
  const [error, setError] = useState('')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  const load = useCallback(async () => {
    try {
      const res = await fetchMetrics()
      setData(res)
      setLastUpdated(new Date())
      setError('')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Erreur inconnue')
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (!autoRefresh) return
    const id = setInterval(load, 30_000)
    return () => clearInterval(id)
  }, [autoRefresh, load])

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-gray-950">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Dashboard métriques</h2>
          <div className="flex items-center gap-4">
            {lastUpdated && (
              <span className="text-xs text-gray-500">
                Mis à jour à {lastUpdated.toLocaleTimeString()}
              </span>
            )}
            <label className="flex items-center gap-2 text-xs text-gray-400 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={e => setAutoRefresh(e.target.checked)}
                className="accent-indigo-500"
              />
              Auto-refresh 30s
            </label>
            <button
              onClick={load}
              className="text-xs px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-colors"
            >
              Actualiser
            </button>
          </div>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-700 rounded-xl p-4 text-sm text-red-300">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {AGENTS.map(a => (
            <AgentCard
              key={a.id}
              label={a.label}
              color={a.color}
              data={data?.agents[a.id]}
              eval={data?.eval[a.id]}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
