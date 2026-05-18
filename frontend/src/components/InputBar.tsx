import { useRef, useState, type KeyboardEvent } from 'react'
import type { AgentType } from '../api/agents'
import type { PendingDoc } from '../hooks/useChat'

interface Props {
  agent: AgentType
  loading: boolean
  uploading: boolean
  pendingDoc: PendingDoc | null
  onSend: (text: string) => void
  onReset: () => void
  onAttach: (file: File) => void
  onDetach: () => void
}

const ACCEPT = '.txt,.md,.py,.js,.ts,.tsx,.jsx,.mjs,.json,.csv,.yaml,.yml,.toml,.html,.css,.sh,.sql,.xml,.rst,.pdf,.docx'

export function InputBar({ agent, loading, uploading, pendingDoc, onSend, onReset, onAttach, onDetach }: Props) {
  const [input, setInput] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)

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

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onAttach(file)
    // Reset input so the same file can be re-selected if detached
    e.target.value = ''
  }

  const accentClass =
    agent === 'dev-senior'
      ? 'bg-dev-600 hover:bg-dev-700 disabled:bg-dev-700/50'
      : 'bg-biz-600 hover:bg-biz-700 disabled:bg-biz-700/50'

  const busy = loading || uploading

  return (
    <div className="border-t border-gray-800 bg-gray-900 p-4">
      {/* Chip fichier joint */}
      {pendingDoc && (
        <div className="flex items-center gap-2 mb-2">
          <span className="flex items-center gap-1.5 bg-gray-700 text-gray-200 text-xs rounded-lg px-3 py-1.5 max-w-xs truncate">
            <span>📎</span>
            <span className="truncate">{pendingDoc.filename}</span>
          </span>
          <button
            onClick={onDetach}
            className="text-gray-500 hover:text-gray-300 text-xs transition-colors"
            title="Retirer le fichier"
          >
            ✕
          </button>
        </div>
      )}

      <div className="flex items-end gap-3">
        {/* Bouton trombone */}
        <button
          onClick={() => fileRef.current?.click()}
          disabled={busy}
          title="Joindre un fichier"
          className="shrink-0 bg-gray-700 hover:bg-gray-600 disabled:opacity-40 text-gray-300 rounded-xl px-3 py-3 text-sm transition-colors disabled:cursor-not-allowed"
        >
          {uploading ? (
            <span className="inline-block w-4 h-4 border-2 border-gray-400/30 border-t-gray-400 rounded-full animate-spin" />
          ) : (
            '📎'
          )}
        </button>

        <input
          ref={fileRef}
          type="file"
          accept={ACCEPT}
          className="hidden"
          onChange={handleFileChange}
        />

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
