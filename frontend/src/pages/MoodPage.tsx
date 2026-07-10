import { FormEvent, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { logMood, getMoodTrends, getMoodForecast } from '../lib/moodApi'

const MOOD_LABELS = ['happy', 'sad', 'angry', 'anxious', 'lonely', 'neutral', 'excited', 'frustrated']

export default function MoodPage() {
  const queryClient = useQueryClient()
  const [moodLabel, setMoodLabel] = useState('neutral')
  const [moodScore, setMoodScore] = useState(5)
  const [note, setNote] = useState('')
  const [saved, setSaved] = useState(false)

  const { data: trends } = useQuery({ queryKey: ['moodTrends'], queryFn: () => getMoodTrends('weekly') })
  const { data: forecast } = useQuery({ queryKey: ['moodForecast'], queryFn: getMoodForecast })

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    await logMood({
      mood_label: moodLabel,
      mood_score: moodScore,
      note: note || undefined,
      logged_date: new Date().toISOString().split('T')[0],
    })
    setSaved(true)
    setNote('')
    queryClient.invalidateQueries({ queryKey: ['moodTrends'] })
    queryClient.invalidateQueries({ queryKey: ['moodForecast'] })
    setTimeout(() => setSaved(false), 2000)
  }

  const chartData = (trends?.points || []).map((p) => ({
    date: p.logged_date.slice(5), // MM-DD
    score: p.mood_score,
  }))

  return (
    <div className="h-full overflow-y-auto px-8 py-8 max-w-3xl mx-auto space-y-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-lamp-500 mb-2">how are you, today</p>
        <h1 className="font-display text-3xl text-ink-100">Mood check-in</h1>
      </div>

      <form onSubmit={handleSubmit} className="bg-dusk-800 border border-dusk-700 rounded-2xl p-6 space-y-5">
        <div>
          <label className="block text-xs text-ink-400 mb-2">What best describes it?</label>
          <div className="flex flex-wrap gap-2">
            {MOOD_LABELS.map((label) => (
              <button
                key={label}
                type="button"
                onClick={() => setMoodLabel(label)}
                className={`px-3 py-1.5 rounded-full text-sm capitalize transition-colors ${
                  moodLabel === label
                    ? 'bg-lamp-500 text-dusk-950'
                    : 'bg-dusk-900 text-ink-300 border border-dusk-700 hover:border-lamp-500'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="flex items-center justify-between text-xs text-ink-400 mb-2">
            <span>Intensity</span>
            <span className="font-mono text-lamp-500">{moodScore}/10</span>
          </label>
          <input
            type="range"
            min={1}
            max={10}
            value={moodScore}
            onChange={(e) => setMoodScore(Number(e.target.value))}
            className="w-full accent-lamp-500"
          />
        </div>

        <div>
          <label className="block text-xs text-ink-400 mb-2">Anything you want to note? (optional)</label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            className="w-full bg-dusk-900 border border-dusk-700 rounded-lg px-3 py-2 text-sm text-ink-100 focus:border-lamp-500 outline-none transition-colors resize-none"
            placeholder="Optional context…"
          />
        </div>

        <button
          type="submit"
          className="bg-lamp-500 text-dusk-950 font-medium px-5 py-2.5 rounded-full hover:bg-lamp-400 transition-colors"
        >
          {saved ? 'Saved ✓' : 'Log today\u2019s mood'}
        </button>
      </form>

      <div className="bg-dusk-800 border border-dusk-700 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-lg text-ink-100">This week</h2>
          {trends?.average_score != null && (
            <span className="text-xs font-mono text-ink-400">avg {trends.average_score}/10</span>
          )}
        </div>
        {chartData.length === 0 ? (
          <p className="text-sm text-ink-400">No mood logs yet this week — log one above to start the chart.</p>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2A2C52" />
              <XAxis dataKey="date" stroke="#A8A9C4" fontSize={12} />
              <YAxis domain={[1, 10]} stroke="#A8A9C4" fontSize={12} />
              <Tooltip contentStyle={{ background: '#1F2140', border: '1px solid #2A2C52', borderRadius: 8 }} />
              <Line type="monotone" dataKey="score" stroke="#E8A854" strokeWidth={2} dot={{ fill: '#E8A854' }} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {forecast?.forecast?.length > 0 && (
        <div className="bg-dusk-800 border border-dusk-700 rounded-2xl p-6">
          <h2 className="font-display text-lg text-ink-100 mb-1">Next few days</h2>
          <p className="text-xs text-ink-400 mb-4 font-mono">
            {forecast.model === 'naive_moving_average_fallback'
              ? 'based on your recent average (forecast model warms up with more history)'
              : 'from the mood forecasting model'}
          </p>
          <div className="flex gap-4">
            {forecast.forecast.map((f: { day_offset: number; predicted_score: number }) => (
              <div key={f.day_offset} className="text-center">
                <p className="text-2xl font-display text-lamp-400">{f.predicted_score}</p>
                <p className="text-xs text-ink-400">+{f.day_offset}d</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
