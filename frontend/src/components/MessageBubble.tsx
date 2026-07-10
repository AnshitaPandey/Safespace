import { Message } from '../lib/chatApi'

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  const isSafetyCard = message.role === 'assistant' && message.safety_flag

  if (isSafetyCard) {
    return (
      <div className="flex justify-start">
        <div className="max-w-[80%] bg-sage-500/10 border border-sage-500/40 rounded-2xl rounded-tl-sm px-4 py-3">
          <p className="text-xs font-mono uppercase tracking-wide text-sage-400 mb-1.5">
            support resources
          </p>
          <p className="text-sm text-ink-100 whitespace-pre-line leading-relaxed">{message.content}</p>
        </div>
      </div>
    )
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-line ${
          isUser
            ? 'bg-lamp-500 text-dusk-950 rounded-tr-sm'
            : 'bg-dusk-800 border border-dusk-700 text-ink-100 rounded-tl-sm'
        }`}
      >
        {message.content}
      </div>
    </div>
  )
}
