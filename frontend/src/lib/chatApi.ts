import { api } from './api'

export type PersonalityType =
  | 'supportive_friend'
  | 'mentor'
  | 'career_coach'
  | 'study_buddy'
  | 'reflective_listener'

export interface Chat {
  id: string
  title: string | null
  personality_type: PersonalityType
  created_at: string
  last_message_at: string | null
  is_archived: boolean
}

export interface Message {
  id: string
  chat_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  safety_flag: boolean
  safety_risk_level: string | null
  created_at: string
}

export async function listChats(): Promise<Chat[]> {
  const { data } = await api.get<Chat[]>('/api/v1/chats')
  return data
}

export async function createChat(personalityType: PersonalityType, title?: string): Promise<Chat> {
  const { data } = await api.post<Chat>('/api/v1/chats', {
    personality_type: personalityType,
    title,
  })
  return data
}

export async function getChatMessages(chatId: string): Promise<Message[]> {
  const { data } = await api.get<Message[]>(`/api/v1/chats/${chatId}/messages`)
  return data
}
