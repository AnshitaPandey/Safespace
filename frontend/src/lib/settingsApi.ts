import { api } from './api'

export interface Memory {
  id: string
  memory_type: string
  content: string
  importance_score: number
  access_count: number
  created_at: string
}

export interface Goal {
  id: string
  title: string
  description: string | null
  target_date: string | null
  is_completed: boolean
  completed_at: string | null
  created_at: string
}

export interface Streak {
  activity_type: string
  current_streak: number
  longest_streak: number
  last_activity_date: string | null
}

export async function listMemories(): Promise<Memory[]> {
  const { data } = await api.get<Memory[]>('/api/v1/memories')
  return data
}

export async function deleteMemory(id: string): Promise<void> {
  await api.delete(`/api/v1/memories/${id}`)
}

export async function listGoals(): Promise<Goal[]> {
  const { data } = await api.get<Goal[]>('/api/v1/goals')
  return data
}

export async function createGoal(payload: { title: string; description?: string; target_date?: string }): Promise<Goal> {
  const { data } = await api.post<Goal>('/api/v1/goals', payload)
  return data
}

export async function toggleGoalComplete(id: string, isCompleted: boolean): Promise<Goal> {
  const { data } = await api.patch<Goal>(`/api/v1/goals/${id}`, { is_completed: isCompleted })
  return data
}

export async function listStreaks(): Promise<Streak[]> {
  const { data } = await api.get<Streak[]>('/api/v1/streaks')
  return data
}
