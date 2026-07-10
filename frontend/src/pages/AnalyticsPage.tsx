import { useQuery } from '@tanstack/react-query'
import { getWeeklyReport, getEmotionalPatterns } from '../lib/analyticsApi'

export default function AnalyticsPage() {
  const { data: report, isLoading: reportLoading } = useQuery({
    queryKey: ['weeklyReport'],
    queryFn: getWeeklyReport,
    retry: false,
  })
  const { data: patterns } = useQuery({
    queryKey: ['emotionalPatterns'],
    queryFn: () => getEmotionalPatterns(30),
  })

  return (
    <div className="h-full overflow-y-auto px-8 py-8 max-w-3xl mx-auto space-y-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-widest text-lamp-500 mb-2">the bigger picture</p>
        <h1 className="font-display text-3xl text-ink-100">Analytics</h1>
      </div>

      <div className="bg-dusk-800 border border-dusk-700 rounded-2xl p-6">
        <h2 className="font-display text-lg text-ink-100 mb-3">This week's reflection</h2>
        {reportLoading ? (
          <p className="text-sm text-ink-400 font-mono animate-pulse">putting this together…</p>
        ) : report?.generated_report ? (
          <>
            <p className="text-sm text-ink-100 leading-relaxed mb-4">{report.generated_report}</p>
            <div className="flex gap-6 text-xs text-ink-400 font-mono">
              {report.avg_mood_score != null && <span>avg mood {report.avg_mood_score}/10</span>}
              {report.dominant_emotion && <span>most common: {report.dominant_emotion}</span>}
              <span>{report.message_count} messages this period</span>
            </div>
          </>
        ) : (
          <p className="text-sm text-ink-400">
            Not enough activity yet to generate a weekly reflection — log a mood or chat a bit more.
          </p>
        )}
      </div>

      <div className="bg-dusk-800 border border-dusk-700 rounded-2xl p-6">
        <h2 className="font-display text-lg text-ink-100 mb-4">Mood distribution (last 30 days)</h2>
        {patterns && Object.keys(patterns.mood_label_distribution).length > 0 ? (
          <div className="space-y-2">
            {Object.entries(patterns.mood_label_distribution as Record<string, number>)
              .sort(([, a], [, b]) => b - a)
              .map(([label, count]) => {
                const pct = (count / patterns.total_logs) * 100
                return (
                  <div key={label}>
                    <div className="flex justify-between text-xs text-ink-300 mb-1 capitalize">
                      <span>{label}</span>
                      <span className="font-mono text-ink-400">{count}</span>
                    </div>
                    <div className="h-1.5 bg-dusk-900 rounded-full overflow-hidden">
                      <div className="h-full bg-lamp-500" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                )
              })}
          </div>
        ) : (
          <p className="text-sm text-ink-400">No mood logs in this window yet.</p>
        )}
      </div>
    </div>
  )
}
