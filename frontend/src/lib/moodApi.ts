import { api } from './api'

export interface MoodLog {
  id: string
  mood_label: string
  mood_score: number
  note: string | null
  logged_date: string
}

export interface MoodTrendPoint {
  logged_date: string
  mood_score: number
  mood_label: string
}

export interface MoodTrends {
  period: string
  points: MoodTrendPoint[]
  average_score: number | null
}

export async function logMood(payload: {
  mood_label: string
  mood_score: number
  note?: string
  logged_date: string
}): Promise<MoodLog> {
  const { data } = await api.post<MoodLog>('/api/v1/mood', payload)
  return data
}

export async function getMoodTrends(period: 'weekly' | 'monthly' = 'weekly'): Promise<MoodTrends> {
  const { data } = await api.get<MoodTrends>('/api/v1/mood/trends', { params: { period } })
  return data
}

export async function getMoodForecast() {
  const { data } = await api.get('/api/v1/analytics/mood-forecast')
  return data
}
