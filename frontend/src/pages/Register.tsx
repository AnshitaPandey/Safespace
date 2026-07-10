import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (password.length < 8) {
      setError('Password needs to be at least 8 characters.')
      return
    }
    setLoading(true)
    try {
      await register(email, password, displayName || undefined)
      navigate('/app/chat')
    } catch {
      setError('Could not create an account with that email.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-sm">
        <Link to="/" className="font-display text-lg text-ink-100 block text-center mb-10">
          SafeSpace
        </Link>
        <div className="bg-dusk-800 border border-dusk-700 rounded-2xl p-8">
          <h1 className="font-display text-2xl text-ink-100 mb-1">Create your space</h1>
          <p className="text-ink-400 text-sm mb-6">Takes less than a minute.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="block text-xs text-ink-400 mb-1.5">
                What should we call you?
              </label>
              <input
                id="name"
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full bg-dusk-900 border border-dusk-700 rounded-lg px-3 py-2.5 text-ink-100 text-sm focus:border-lamp-500 outline-none transition-colors"
                placeholder="First name is fine"
              />
            </div>
            <div>
              <label htmlFor="email" className="block text-xs text-ink-400 mb-1.5">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-dusk-900 border border-dusk-700 rounded-lg px-3 py-2.5 text-ink-100 text-sm focus:border-lamp-500 outline-none transition-colors"
                placeholder="you@example.com"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-xs text-ink-400 mb-1.5">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-dusk-900 border border-dusk-700 rounded-lg px-3 py-2.5 text-ink-100 text-sm focus:border-lamp-500 outline-none transition-colors"
                placeholder="At least 8 characters"
              />
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-lamp-500 text-dusk-950 font-medium py-2.5 rounded-lg hover:bg-lamp-400 transition-colors disabled:opacity-60"
            >
              {loading ? 'Creating your space…' : 'Create account'}
            </button>
          </form>

          <p className="text-center text-sm text-ink-400 mt-6">
            Already have a space?{' '}
            <Link to="/login" className="text-lamp-500 hover:text-lamp-400">
              Log in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
