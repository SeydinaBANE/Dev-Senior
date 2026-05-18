import { useState, type KeyboardEvent } from 'react'
import type { AgentType } from '../api/agents'

interface Props {
  agent: AgentType
  loading: boolean
  onSend: (text: string) => void
  onReset: () => void
}

export function InputBar({ agent, loading, onSend, onReset }: Props) {
  const [input, setInput] = useState('')

  const submit = () => {
    if (!input.trim() || loading) return
    onSend(input.trim())
    setInput('')
  }

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const accentClass =
    agent === 'dev-senior'
      ? 'bg-dev-600 hover:bg-dev-700 disabled:bg-dev-700/50'
      : 'bg-biz-600 hover:bg-biz-700 disabled:bg-biz-700/50'

  return (
    <div className="border-t border-gray-800 bg-gray-900 p-4">
      <div className="flex items-end gap-3">
        <textarea
          className="flex-1 bg-gray-800 text-gray-100 rounded-xl px-4 py-3 text-sm resize-none outline-none focus:ring-2 focus:ring-gray-600 min-h-[48px] max-h-40 scrollbar-thin"
          placeholder={`Message à ${agent === 'dev-senior' ? 'Dev Senior' : 'Business Manager'}… (Entrée pour envoyer, Maj+Entrée pour un saut de ligne)`}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={onKey}
          rows={1}
          disabled={loading}
        />
        <div className="flex flex-col gap-2">
          <button
            onClick={submit}
            disabled={!input.trim() || loading}
            className={`${accentClass} text-white rounded-xl px-4 py-3 text-sm font-medium transition-colors disabled:cursor-not-allowed`}
          >
            {loading ? (
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              '↑'
            )}
          </button>
          <button
            onClick={onReset}
            title="Nouvelle conversation"
            className="bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-xl px-3 py-2 text-xs transition-colors"
          >
            ↺
          </button>
        </div>
      </div>
    </div>
  )
}
