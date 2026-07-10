import { useCallback, useEffect, useRef, useState } from 'react'

export interface WsAssistantMessage {
  type: 'assistant_message'
  id: string
  content: string
  safety_gated: boolean
  created_at: string
}

interface WsAckMessage {
  type: 'user_message_received'
}

type WsIncoming = WsAssistantMessage | WsAckMessage

const WS_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/^http/, 'ws')

export function useChatSocket(chatId: string | null, onAssistantMessage: (msg: WsAssistantMessage) => void) {
  const socketRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isWaitingForReply, setIsWaitingForReply] = useState(false)

  useEffect(() => {
    if (!chatId) return

    const token = localStorage.getItem('access_token')
    const socket = new WebSocket(`${WS_BASE_URL}/ws/chats/${chatId}?token=${token}`)
    socketRef.current = socket

    socket.onopen = () => setIsConnected(true)
    socket.onclose = () => setIsConnected(false)

    socket.onmessage = (event) => {
      const data: WsIncoming = JSON.parse(event.data)
      if (data.type === 'user_message_received') {
        setIsWaitingForReply(true)
      } else if (data.type === 'assistant_message') {
        setIsWaitingForReply(false)
        onAssistantMessage(data)
      }
    }

    return () => {
      socket.close()
      socketRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chatId])

  const sendMessage = useCallback((content: string) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ content }))
    }
  }, [])

  return { isConnected, isWaitingForReply, sendMessage }
}
