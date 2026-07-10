import { api } from './api'

export interface AnalyticsSnapshot {
  id: string
  period_type: string
  period_start: string
  period_end: string
  avg_mood_score: number | null
  dominant_emotion: string | null
  top_topics: string[] | null
  message_count: number
  generated_report: string | null
  created_at: string
}

export async function getWeeklyReport(): Promise<AnalyticsSnapshot> {
  const { data } = await api.get<AnalyticsSnapshot>('/api/v1/analytics/weekly-report')
  return data
}

export async function getEmotionalPatterns(days = 30) {
  const { data } = await api.get('/api/v1/analytics/emotional-patterns', { params: { days } })
  return data
}
