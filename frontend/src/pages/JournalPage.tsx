import { FormEvent, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createJournalEntry, listJournalEntries, deleteJournalEntry, JournalEntry } from '../lib/journalApi'

export default function JournalPage() {
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const { data: entries = [] } = useQuery({
    queryKey: ['journalEntries'],
    queryFn: listJournalEntries,
    // Summary/themes/reflection questions are filled in asynchronously by a Celery worker —
    // poll briefly after mount so entries update once enrichment lands, without a full
    // websocket for something this infrequent.
    refetchInterval: 8000,
  })

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!draft.trim()) return
    setSubmitting(true)
    try {
      await createJournalEntry(draft)
      setDraft('')
      queryClient.invalidateQueries({ queryKey: ['journalEntries'] })
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id: string) => {
    await deleteJournalEntry(id)
    queryClient.invalidateQueries({ queryKey: ['journalEntries'] })
  }

  return (
    <div className="h-full overflow-y-auto px-8 py-8 max-w-2xl mx-auto space-y-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-lamp-500 mb-2">write it down</p>
        <h1 className="font-display text-3xl text-ink-100">Journal</h1>
      </div>

      <form onSubmit={handleSubmit} className="bg-dusk-800 border border-dusk-700 rounded-2xl p-6">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={6}
          placeholder="What's on your mind today?"
          className="w-full bg-dusk-900 border border-dusk-700 rounded-lg px-3 py-2.5 text-sm text-ink-100 focus:border-lamp-500 outline-none transition-colors resize-none"
        />
        <div className="flex justify-end mt-3">
          <button
            type="submit"
            disabled={!draft.trim() || submitting}
            className="bg-lamp-500 text-dusk-950 font-medium px-5 py-2.5 rounded-full hover:bg-lamp-400 transition-colors disabled:opacity-40"
          >
            {submitting ? 'Saving…' : 'Save entry'}
          </button>
        </div>
      </form>

      <div className="space-y-4">
        {entries.map((entry) => (
          <JournalCard key={entry.id} entry={entry} onDelete={() => handleDelete(entry.id)} />
        ))}
        {entries.length === 0 && (
          <p className="text-sm text-ink-400 text-center py-8">No entries yet — write your first one above.</p>
        )}
      </div>
    </div>
  )
}

function JournalCard({ entry, onDelete }: { entry: JournalEntry; onDelete: () => void }) {
  const [expanded, setExpanded] = useState(false)
  const isEnriched = entry.summary != null

  return (
    <div className="bg-dusk-800 border border-dusk-700 rounded-2xl p-5">
      <div className="flex items-start justify-between mb-2">
        <p className="text-xs text-ink-400 font-mono">
          {new Date(entry.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
        </p>
        <button onClick={onDelete} className="text-xs text-ink-400 hover:text-red-400 transition-colors">
          delete
        </button>
      </div>

      {isEnriched ? (
        <>
          <p className="text-sm text-ink-100 leading-relaxed mb-3">{entry.summary}</p>
          {entry.themes && entry.themes.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {entry.themes.map((theme) => (
                <span key={theme} className="text-xs bg-sage-500/10 text-sage-400 px-2 py-0.5 rounded-full">
                  {theme}
                </span>
              ))}
            </div>
          )}
          <button
            onClick={() => setExpanded((v) => !v)}
            className="text-xs text-lamp-500 hover:text-lamp-400 transition-colors"
          >
            {expanded ? 'Hide original entry' : 'Show original entry & reflection questions'}
          </button>
          {expanded && (
            <div className="mt-3 pt-3 border-t border-dusk-700 space-y-3">
              <p className="text-sm text-ink-300 whitespace-pre-line leading-relaxed">{entry.raw_content}</p>
              {entry.reflection_questions && entry.reflection_questions.length > 0 && (
                <div>
                  <p className="text-xs font-mono uppercase text-ink-400 mb-1.5">worth sitting with</p>
                  <ul className="space-y-1">
                    {entry.reflection_questions.map((q) => (
                      <li key={q} className="text-sm text-ink-300 italic">
                        {q}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div>
          <p className="text-sm text-ink-300 whitespace-pre-line leading-relaxed mb-2">{entry.raw_content}</p>
          <p className="text-xs text-ink-400 font-mono animate-pulse">generating summary…</p>
        </div>
      )}
    </div>
  )
}
