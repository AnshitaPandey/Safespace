import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Register from './pages/Register'
import AppLayout from './pages/AppLayout'
import ChatPage from './pages/ChatPage'
import MoodPage from './pages/MoodPage'
import JournalPage from './pages/JournalPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SettingsPage from './pages/SettingsPage'

function ProtectedRoute({ children }: { children: JSX.Element }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/app/chat" replace />} />
        <Route path="chat" element={<ChatPage />} />
        <Route path="mood" element={<MoodPage />} />
        <Route path="journal" element={<JournalPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      {/* Old Week 1-2 route, kept working for anyone with it bookmarked/linked */}
      <Route path="/dashboard" element={<Navigate to="/app/chat" replace />} />
    </Routes>
  )
}
