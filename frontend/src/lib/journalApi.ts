import { api } from './api'

export interface JournalEntry {
  id: string
  raw_content: string
  summary: string | null
  themes: string[] | null
  reflection_questions: string[] | null
  sentiment_score: number | null
  created_at: string
  updated_at: string
}

export async function createJournalEntry(rawContent: string): Promise<JournalEntry> {
  const { data } = await api.post<JournalEntry>('/api/v1/journal', { raw_content: rawContent })
  return data
}

export async function listJournalEntries(): Promise<JournalEntry[]> {
  const { data } = await api.get<JournalEntry[]>('/api/v1/journal')
  return data
}

export async function getJournalEntry(id: string): Promise<JournalEntry> {
  const { data } = await api.get<JournalEntry>(`/api/v1/journal/${id}`)
  return data
}

export async function deleteJournalEntry(id: string): Promise<void> {
  await api.delete(`/api/v1/journal/${id}`)
}
