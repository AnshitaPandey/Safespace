import { FormEvent, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate('/app/chat')
    } catch {
      setError('That email and password combination did not work.')
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
          <h1 className="font-display text-2xl text-ink-100 mb-1">Welcome back</h1>
          <p className="text-ink-400 text-sm mb-6">Good to see you again.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
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
              <div className="flex items-center justify-between mb-1.5">
                <label htmlFor="password" className="block text-xs text-ink-400">
                  Password
                </label>
                <Link to="/reset-password" className="text-xs text-lamp-500 hover:text-lamp-400">
                  Forgot?
                </Link>
              </div>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-dusk-900 border border-dusk-700 rounded-lg px-3 py-2.5 text-ink-100 text-sm focus:border-lamp-500 outline-none transition-colors"
                placeholder="••••••••"
              />
            </div>

            {error && <p className="text-sm text-red-400">{error}</p>}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-lamp-500 text-dusk-950 font-medium py-2.5 rounded-lg hover:bg-lamp-400 transition-colors disabled:opacity-60"
            >
              {loading ? 'Logging in…' : 'Log in'}
            </button>
          </form>

          <p className="text-center text-sm text-ink-400 mt-6">
            New here?{' '}
            <Link to="/register" className="text-lamp-500 hover:text-lamp-400">
              Create an account
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
