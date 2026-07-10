import { FormEvent, useEffect, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { Chat, Message, PersonalityType, createChat, getChatMessages, listChats } from '../lib/chatApi'
import { useChatSocket } from '../hooks/useChatSocket'
import MessageBubble from '../components/MessageBubble'
import PersonalitySelector from '../components/PersonalitySelector'

export default function Dashboard() {
  const { logout } = useAuth()
  const queryClient = useQueryClient()
  const [activeChatId, setActiveChatId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  const { data: chats = [] } = useQuery({ queryKey: ['chats'], queryFn: listChats })

  useEffect(() => {
    if (!activeChatId && chats.length > 0) {
      setActiveChatId(chats[0].id)
    }
  }, [chats, activeChatId])

  useEffect(() => {
    if (!activeChatId) {
      setMessages([])
      return
    }
    getChatMessages(activeChatId).then(setMessages)
  }, [activeChatId])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  const { isWaitingForReply, sendMessage } = useChatSocket(activeChatId, (assistantMsg) => {
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsg.id,
        chat_id: activeChatId!,
        role: 'assistant',
        content: assistantMsg.content,
        safety_flag: assistantMsg.safety_gated,
        safety_risk_level: assistantMsg.safety_gated ? 'high' : null,
        created_at: assistantMsg.created_at,
      },
    ])
  })

  const handleStartChat = async (personality: PersonalityType) => {
    const chat = await createChat(personality)
    queryClient.setQueryData<Chat[]>(['chats'], (prev = []) => [chat, ...prev])
    setActiveChatId(chat.id)
  }

  const handleSend = (e: FormEvent) => {
    e.preventDefault()
    const content = draft.trim()
    if (!content || !activeChatId) return

    setMessages((prev) => [
      ...prev,
      {
        id: `temp-${Date.now()}`,
        chat_id: activeChatId,
        role: 'user',
        content,
        safety_flag: false,
        safety_risk_level: null,
        created_at: new Date().toISOString(),
      },
    ])
    sendMessage(content)
    setDraft('')
  }

  const activeChat = chats.find((c) => c.id === activeChatId)

  return (
    <div className="h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-dusk-950 border-r border-dusk-700 flex flex-col">
        <div className="px-4 py-5 flex items-center justify-between">
          <span className="font-display text-lg text-ink-100">SafeSpace</span>
        </div>
        <div className="px-3 pb-3">
          <NewChatMenu onSelect={handleStartChat} />
        </div>
        <div className="flex-1 overflow-y-auto px-2 space-y-1">
          {chats.map((chat) => (
            <button
              key={chat.id}
              onClick={() => setActiveChatId(chat.id)}
              className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors ${
                chat.id === activeChatId
                  ? 'bg-dusk-800 text-ink-100'
                  : 'text-ink-400 hover:bg-dusk-800/50 hover:text-ink-100'
              }`}
            >
              <p className="truncate">{chat.title || personalityLabel(chat.personality_type)}</p>
            </button>
          ))}
        </div>
        <div className="p-3 border-t border-dusk-700">
          <button
            onClick={() => logout()}
            className="w-full text-xs text-ink-400 hover:text-ink-100 transition-colors py-2"
          >
            Log out
          </button>
        </div>
      </aside>

      {/* Chat window */}
      <main className="flex-1 flex flex-col">
        {!activeChatId ? (
          <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
            <p className="font-mono text-xs uppercase tracking-widest text-lamp-500 mb-4">
              start somewhere
            </p>
            <h2 className="font-display text-2xl text-ink-100 mb-6">Who do you want to talk to today?</h2>
            <PersonalitySelector onSelect={handleStartChat} />
          </div>
        ) : (
          <>
            <div className="border-b border-dusk-700 px-6 py-4">
              <p className="text-sm text-ink-400 font-mono">
                {activeChat ? personalityLabel(activeChat.personality_type) : ''}
              </p>
            </div>

            <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6 space-y-3">
              {messages.map((m) => (
                <MessageBubble key={m.id} message={m} />
              ))}
              {isWaitingForReply && (
                <div className="flex justify-start">
                  <div className="bg-dusk-800 border border-dusk-700 rounded-2xl rounded-tl-sm px-4 py-2.5">
                    <span className="inline-flex gap-1">
                      <span className="w-1.5 h-1.5 bg-ink-400 rounded-full animate-pulse" />
                      <span className="w-1.5 h-1.5 bg-ink-400 rounded-full animate-pulse [animation-delay:0.2s]" />
                      <span className="w-1.5 h-1.5 bg-ink-400 rounded-full animate-pulse [animation-delay:0.4s]" />
                    </span>
                  </div>
                </div>
              )}
            </div>

            <form onSubmit={handleSend} className="border-t border-dusk-700 px-6 py-4 flex gap-3">
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Say whatever's on your mind…"
                className="flex-1 bg-dusk-800 border border-dusk-700 rounded-full px-4 py-2.5 text-sm text-ink-100 focus:border-lamp-500 outline-none transition-colors"
              />
              <button
                type="submit"
                disabled={!draft.trim()}
                className="bg-lamp-500 text-dusk-950 font-medium px-5 py-2.5 rounded-full hover:bg-lamp-400 transition-colors disabled:opacity-40"
              >
                Send
              </button>
            </form>
          </>
        )}
      </main>
    </div>
  )
}

function NewChatMenu({ onSelect }: { onSelect: (p: PersonalityType) => void }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full bg-lamp-500 text-dusk-950 text-sm font-medium py-2 rounded-lg hover:bg-lamp-400 transition-colors"
      >
        + New chat
      </button>
      {open && (
        <div className="absolute z-10 top-full mt-2 left-0 bg-dusk-800 border border-dusk-700 rounded-xl p-2 w-56 space-y-1">
          {(
            [
              'supportive_friend',
              'mentor',
              'career_coach',
              'study_buddy',
              'reflective_listener',
            ] as PersonalityType[]
          ).map((p) => (
            <button
              key={p}
              onClick={() => {
                onSelect(p)
                setOpen(false)
              }}
              className="w-full text-left text-sm text-ink-300 hover:text-ink-100 hover:bg-dusk-700 rounded-lg px-2 py-1.5 transition-colors"
            >
              {personalityLabel(p)}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

function personalityLabel(p: PersonalityType): string {
  const labels: Record<PersonalityType, string> = {
    supportive_friend: 'Supportive Friend',
    mentor: 'Mentor',
    career_coach: 'Career Coach',
    study_buddy: 'Study Buddy',
    reflective_listener: 'Reflective Listener',
  }
  return labels[p]
}
