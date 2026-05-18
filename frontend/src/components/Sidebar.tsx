import type { AgentType } from '../api/agents'

interface Props {
  active: AgentType
  onChange: (agent: AgentType) => void
}

const agents: { id: AgentType; label: string; desc: string; icon: string; color: string }[] = [
  {
    id: 'dev-senior',
    label: 'Dev Senior',
    desc: 'Architecture, debug, code review',
    icon: '💻',
    color: 'dev',
  },
  {
    id: 'biz-manager',
    label: 'Business Manager',
    desc: 'SEO, marketing, contenus, CRM',
    icon: '📊',
    color: 'biz',
  },
]

export function Sidebar({ active, onChange }: Props) {
  return (
    <aside className="w-64 shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-sm font-semibold text-gray-400 uppercase tracking-widest">
          Agents IA
        </h1>
      </div>

      <nav className="flex-1 p-3 space-y-2">
        {agents.map(a => (
          <button
            key={a.id}
            onClick={() => onChange(a.id)}
            className={`w-full text-left rounded-xl p-3 transition-all ${
              active === a.id
                ? a.color === 'dev'
                  ? 'bg-dev-700 text-white'
                  : 'bg-biz-700 text-white'
                : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span className="text-lg">{a.icon}</span>
              <span className="font-medium text-sm">{a.label}</span>
            </div>
            <p className="text-xs opacity-75 leading-tight">{a.desc}</p>
          </button>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-800">
        <p className="text-xs text-gray-600">Propulsé par OpenRouter</p>
      </div>
    </aside>
  )
}
