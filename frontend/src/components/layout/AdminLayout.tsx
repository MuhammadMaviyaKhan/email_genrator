import { NavLink, useNavigate, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  Mail,
  FileText,
  LogOut,
  Menu,
  X,
  Shield,
  Activity,
} from 'lucide-react'
import { useState } from 'react'
import { ADMIN_TOKEN_KEY } from '@/utils/constants'
import { cn } from '@/utils/cn'
import { toast } from 'react-toastify'

const navItems = [
  { to: '/admin', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/admin/emails', icon: Mail, label: 'Emails' },
  { to: '/admin/logs', icon: FileText, label: 'Logs' },
]

export default function AdminLayout() {
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleLogout = () => {
    localStorage.removeItem(ADMIN_TOKEN_KEY)
    toast.success('Logged out from admin')
    navigate('/admin/login')
  }

  return (
    <div className="min-h-screen flex">
      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-50 w-64 bg-dark-900/95 backdrop-blur-xl border-r border-dark-800/50',
          'transform transition-transform duration-300 lg:transform-none',
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex items-center gap-2 p-6 border-b border-dark-800/50">
          <div className="p-2 rounded-xl bg-gradient-to-br from-primary-500 to-cyan-500 shadow-lg shadow-primary-500/30">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold gradient-text">Admin Panel</span>
        </div>

        <nav className="p-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all',
                  isActive
                    ? 'bg-primary-500/20 text-primary-300 shadow-lg shadow-primary-500/10'
                    : 'text-dark-400 hover:text-dark-100 hover:bg-dark-800/50'
                )
              }
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-dark-800/50">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-dark-400 hover:text-red-400 hover:bg-red-500/10 transition-all w-full"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </aside>

      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 border-b border-dark-800/50 bg-dark-950/80 backdrop-blur-xl">
          <div className="flex items-center justify-between px-4 sm:px-6 py-4">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 rounded-xl bg-dark-800 hover:bg-dark-700 transition-colors"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <h1 className="text-lg font-semibold text-dark-100 flex items-center gap-2">
              <Activity className="w-5 h-5 text-primary-400" />
              TempMail Pro Admin
            </h1>
          </div>
        </header>

        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-x-hidden">
          <Outlet />
        </main>
      </div>
    </div>
  )
}