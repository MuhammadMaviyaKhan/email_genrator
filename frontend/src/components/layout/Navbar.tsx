import { Link, useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Moon, Sun, Menu, X, Mail, LogOut, Copy } from 'lucide-react'
import { useState } from 'react'
import { useTheme } from '@/context/ThemeContext'
import { apiClient } from '@/services/api'
import { STORAGE_KEYS } from '@/utils/constants'
import { copyToClipboard } from '@/utils/cn'
import { toast } from 'react-toastify'
import Button from '@/components/ui/Button'

export default function Navbar() {
  const { resolvedTheme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)

  const email = localStorage.getItem(STORAGE_KEYS.EMAIL_DATA)
    ? JSON.parse(localStorage.getItem(STORAGE_KEYS.EMAIL_DATA) || '{}')
    : null

  const handleLogout = () => {
    apiClient.clearToken()
    localStorage.removeItem(STORAGE_KEYS.EMAIL_DATA)
    localStorage.removeItem(STORAGE_KEYS.EMAIL_ID)
    navigate('/')
    toast.success('Logged out successfully')
  }

  const copyEmail = async () => {
    if (email?.email) {
      await copyToClipboard(email.email)
      toast.success('Email copied to clipboard')
    }
  }

  return (
    <nav className="sticky top-0 z-40 border-b border-dark-800/50 bg-dark-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-2">
            <Link to="/" className="flex items-center gap-2">
              <div className="p-2 rounded-xl bg-gradient-to-br from-primary-500 to-cyan-500 shadow-lg shadow-primary-500/30">
                <Mail className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold gradient-text hidden sm:block">TempMail Pro</span>
            </Link>
          </div>

          <div className="hidden md:flex items-center gap-1">
            <NavLink to="/" active={location.pathname === '/'}>
              Home
            </NavLink>
            <NavLink to="/generate" active={location.pathname === '/generate'}>
              Generate
            </NavLink>
            {email && (
              <NavLink to="/inbox" active={location.pathname === '/inbox'}>
                Inbox
              </NavLink>
            )}
          </div>

          <div className="flex items-center gap-2">
            {email && (
              <button
                onClick={copyEmail}
                className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-dark-800 hover:bg-dark-700 transition-colors text-sm"
              >
                <span className="text-dark-300 max-w-[200px] truncate">{email.email}</span>
                <Copy className="w-3.5 h-3.5 text-dark-400" />
              </button>
            )}

            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl bg-dark-800 hover:bg-dark-700 transition-colors"
              aria-label="Toggle theme"
            >
              {resolvedTheme === 'dark' ? (
                <Sun className="w-5 h-5 text-yellow-400" />
              ) : (
                <Moon className="w-5 h-5 text-primary-400" />
              )}
            </button>

            {email && (
              <Button variant="ghost" size="sm" onClick={handleLogout}>
                <LogOut className="w-4 h-4" />
                <span className="hidden sm:block">Logout</span>
              </Button>
            )}

            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-xl bg-dark-800 hover:bg-dark-700 transition-colors"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {mobileOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className="md:hidden border-t border-dark-800/50 bg-dark-900/95 backdrop-blur-xl"
        >
          <div className="px-4 py-3 flex flex-col gap-1">
            <MobileNavLink to="/" onClick={() => setMobileOpen(false)}>
              Home
            </MobileNavLink>
            <MobileNavLink to="/generate" onClick={() => setMobileOpen(false)}>
              Generate
            </MobileNavLink>
            {email && (
              <MobileNavLink to="/inbox" onClick={() => setMobileOpen(false)}>
                Inbox
              </MobileNavLink>
            )}
          </div>
        </motion.div>
      )}
    </nav>
  )
}

function NavLink({ to, active, children }: { to: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className={`px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
        active
          ? 'bg-dark-800 text-primary-400'
          : 'text-dark-300 hover:text-dark-100 hover:bg-dark-800/50'
      }`}
    >
      {children}
    </Link>
  )
}

function MobileNavLink({ to, onClick, children }: { to: string; onClick: () => void; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className="px-4 py-2.5 rounded-xl text-dark-300 hover:text-dark-100 hover:bg-dark-800/50 transition-colors"
    >
      {children}
    </Link>
  )
}