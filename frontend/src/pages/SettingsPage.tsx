import { FormEvent, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  listMemories,
  deleteMemory,
  listGoals,
  createGoal,
  toggleGoalComplete,
  listStreaks,
} from '../lib/settingsApi'

export default function SettingsPage() {
  return (
    <div className="h-full overflow-y-auto px-8 py-8 max-w-2xl mx-auto space-y-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-lamp-500 mb-2">your space, your rules</p>
        <h1 className="font-display text-3xl text-ink-100">Settings</h1>
      </div>

      <StreaksSection />
      <GoalsSection />
      <MemoriesSection />
    </div>
  )
}

function StreaksSection() {
  const { data: streaks = [] } = useQuery({ queryKey: ['streaks'], queryFn: listStreaks })
  if (streaks.length === 0) return null

  return (
    <div className="bg-dusk-800 border border-dusk-700 rounded-2xl p-6">
      <h2 className="font-display text-lg text-ink-100 mb-4">Streaks</h2>
      <div className="flex gap-6">
        {streaks.map((s) => (
          <div key={s.activity_type}>
            <p className="text-2xl font-display text-lamp-400">{s.current_streak}</p>
            <p className="text-xs text-ink-400 capitalize">{s.activity_type.replace('_', ' ')}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function GoalsSection() {
  const queryClient = useQueryClient()
  const [title, setTitle] = useState('')
  const { data: goals = [] } = useQuery({ queryKey: ['goals'], queryFn: listGoals })

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    await createGoal({ title })
    setTitle('')
    queryClient.invalidateQueries({ queryKey: ['goals'] })
  }

  const handleToggle = async (id: string, current: boolean) => {
    await toggleGoalComplete(id, !current)
    queryClient.invalidateQueries({ queryKey: ['goals'] })
  }

  return (
    <div className="bg-dusk-800 border border-dusk-700 rounded-2xl p-6">
      <h2 className="font-display text-lg text-ink-100 mb-4">Goals</h2>
      <form onSubmit={handleAdd} className="flex gap-2 mb-4">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Add a goal…"
          className="flex-1 bg-dusk-900 border border-dusk-700 rounded-lg px-3 py-2 text-sm text-ink-100 focus:border-lamp-500 outline-none transition-colors"
        />
        <button
          type="submit"
          className="bg-lamp-500 text-dusk-950 text-sm font-medium px-4 py-2 rounded-lg hover:bg-lamp-400 transition-colors"
        >
          Add
        </button>
      </form>
      <div className="space-y-2">
        {goals.map((g) => (
          <label key={g.id} className="flex items-center gap-3 text-sm">
            <input
              type="checkbox"
              checked={g.is_completed}
              onChange={() => handleToggle(g.id, g.is_completed)}
              className="accent-lamp-500"
            />
            <span className={g.is_completed ? 'text-ink-400 line-through' : 'text-ink-100'}>{g.title}</span>
          </label>
        ))}
        {goals.length === 0 && <p className="text-sm text-ink-400">No goals yet.</p>}
      </div>
    </div>
  )
}

function MemoriesSection() {
  const queryClient = useQueryClient()
  const { data: memories = [] } = useQuery({ queryKey: ['memories'], queryFn: listMemories })

  const handleDelete = async (id: string) => {
    await deleteMemory(id)
    queryClient.invalidateQueries({ queryKey: ['memories'] })
  }

  return (
    <div className="bg-dusk-800 border border-dusk-700 rounded-2xl p-6">
      <h2 className="font-display text-lg text-ink-100 mb-1">What SafeSpace remembers</h2>
      <p className="text-xs text-ink-400 mb-4">
        These are facts picked up from your conversations. Remove anything you'd rather it forgot.
      </p>
      <div className="space-y-2">
        {memories.map((m) => (
          <div key={m.id} className="flex items-start justify-between gap-3 bg-dusk-900 rounded-lg px-3 py-2.5">
            <div>
              <p className="text-sm text-ink-100">{m.content}</p>
              <p className="text-xs text-ink-400 font-mono mt-0.5">{m.memory_type.replace('_', ' ')}</p>
            </div>
            <button
              onClick={() => handleDelete(m.id)}
              className="text-xs text-ink-400 hover:text-red-400 transition-colors shrink-0"
            >
              forget this
            </button>
          </div>
        ))}
        {memories.length === 0 && (
          <p className="text-sm text-ink-400">Nothing remembered yet — it builds up as you chat.</p>
        )}
      </div>
    </div>
  )
}
