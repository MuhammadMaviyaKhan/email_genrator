import { Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { useLocation } from 'react-router-dom'
import Layout from './components/layout/Layout'
import AdminLayout from './components/layout/AdminLayout'
import HomePage from './pages/HomePage'
import GeneratePage from './pages/GeneratePage'
import InboxPage from './pages/InboxPage'
import EmailViewPage from './pages/EmailViewPage'
import AdminLoginPage from './pages/AdminLoginPage'
import AdminDashboard from './pages/AdminDashboard'
import AdminEmails from './pages/AdminEmails'
import AdminLogs from './pages/AdminLogs'
import NotFoundPage from './pages/NotFoundPage'
import { STORAGE_KEYS, ADMIN_TOKEN_KEY } from './utils/constants'
import { apiClient } from './services/api'

function AuthGuard({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem(STORAGE_KEYS.TOKEN)
  if (!token) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}

function AdminGuard({ children }: { children: React.ReactNode }) {
  const adminToken = localStorage.getItem(ADMIN_TOKEN_KEY)
  if (!adminToken) {
    return <Navigate to="/admin/login" replace />
  }
  return <>{children}</>
}

function AnimatedRoutes() {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="generate" element={<GeneratePage />} />
          <Route
            path="inbox"
            element={
              <AuthGuard>
                <InboxPage />
              </AuthGuard>
            }
          />
          <Route
            path="email/:emailId/:messageId"
            element={
              <AuthGuard>
                <EmailViewPage />
              </AuthGuard>
            }
          />
        </Route>

        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route
          path="/admin"
          element={
            <AdminGuard>
              <AdminLayout />
            </AdminGuard>
          }
        >
          <Route index element={<AdminDashboard />} />
          <Route path="emails" element={<AdminEmails />} />
          <Route path="logs" element={<AdminLogs />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </AnimatePresence>
  )
}

export default function App() {
  apiClient.setToken(localStorage.getItem(STORAGE_KEYS.TOKEN))

  return <AnimatedRoutes />
}