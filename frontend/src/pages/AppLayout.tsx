import { NavLink, Outlet } from 'react-router-dom'
import { MessageCircle, Smile, BookOpen, BarChart3, Settings } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { to: '/app/chat', label: 'Chat', icon: MessageCircle },
  { to: '/app/mood', label: 'Mood', icon: Smile },
  { to: '/app/journal', label: 'Journal', icon: BookOpen },
  { to: '/app/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/app/settings', label: 'Settings', icon: Settings },
]

export default function AppLayout() {
  const { logout } = useAuth()

  return (
    <div className="h-screen flex">
      <nav className="w-16 bg-dusk-950 border-r border-dusk-700 flex flex-col items-center py-4">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-lamp-400 to-lamp-600 mb-6" />
        <div className="flex-1 flex flex-col gap-2">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              title={label}
              className={({ isActive }) =>
                `w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${
                  isActive ? 'bg-dusk-800 text-lamp-500' : 'text-ink-400 hover:text-ink-100 hover:bg-dusk-800/50'
                }`
              }
            >
              <Icon size={18} strokeWidth={1.75} />
            </NavLink>
          ))}
        </div>
        <button
          onClick={() => logout()}
          title="Log out"
          className="w-10 h-10 flex items-center justify-center rounded-lg text-ink-400 hover:text-ink-100 hover:bg-dusk-800/50 transition-colors text-xs"
        >
          ⏻
        </button>
      </nav>

      <div className="flex-1 min-w-0">
        <Outlet />
      </div>
    </div>
  )
}
