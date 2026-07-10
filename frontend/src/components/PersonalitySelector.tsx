import { PersonalityType } from '../lib/chatApi'

const PERSONALITIES: { value: PersonalityType; label: string; description: string }[] = [
  { value: 'supportive_friend', label: 'Supportive Friend', description: 'Warm, casual, validating' },
  { value: 'mentor', label: 'Mentor', description: 'Reflective, growth-oriented' },
  { value: 'career_coach', label: 'Career Coach', description: 'Structured, action-oriented' },
  { value: 'study_buddy', label: 'Study Buddy', description: 'Encouraging, accountability-focused' },
  { value: 'reflective_listener', label: 'Reflective Listener', description: 'Mostly listens, asks questions' },
]

export default function PersonalitySelector({
  onSelect,
}: {
  onSelect: (personality: PersonalityType) => void
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
      {PERSONALITIES.map((p) => (
        <button
          key={p.value}
          onClick={() => onSelect(p.value)}
          className="text-left bg-dusk-800 border border-dusk-700 rounded-xl px-4 py-3 hover:border-lamp-500 transition-colors"
        >
          <p className="font-display text-base text-ink-100">{p.label}</p>
          <p className="text-xs text-ink-400 mt-0.5">{p.description}</p>
        </button>
      ))}
    </div>
  )
}
