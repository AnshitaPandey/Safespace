import { createContext, useContext, useState, ReactNode } from 'react'
import { api } from '../lib/api'

interface AuthContextType {
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, displayName?: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    !!localStorage.getItem('access_token'),
  )

  const storeTokens = (accessToken: string, refreshToken: string) => {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    setIsAuthenticated(true)
  }

  const login = async (email: string, password: string) => {
    const { data } = await api.post('/api/v1/auth/login', { email, password })
    storeTokens(data.access_token, data.refresh_token)
  }

  const register = async (email: string, password: string, displayName?: string) => {
    const { data } = await api.post('/api/v1/auth/register', {
      email,
      password,
      display_name: displayName,
    })
    storeTokens(data.access_token, data.refresh_token)
  }

  const logout = async () => {
    const refreshToken = localStorage.getItem('refresh_token')
    if (refreshToken) {
      try {
        await api.post('/api/v1/auth/logout', { refresh_token: refreshToken })
      } catch {
        // best-effort — clear local state regardless
      }
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setIsAuthenticated(false)
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
