import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Shield, Lock, Mail } from 'lucide-react'
import { apiClient } from '@/services/api'
import { ADMIN_TOKEN_KEY } from '@/utils/constants'
import { toast } from 'react-toastify'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'

export default function AdminLoginPage() {
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await apiClient.post<{ access_token: string }>('/auth/admin/login', {
        password,
      })
      localStorage.setItem(ADMIN_TOKEN_KEY, response.access_token)
      toast.success('Admin login successful')
      navigate('/admin')
    } catch (error: any) {
      toast.error(error.detail || 'Invalid admin password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="animated-bg absolute inset-0 pointer-events-none" />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative z-10 w-full max-w-md"
      >
        <Card glass className="p-8">
          <div className="text-center mb-8">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200 }}
              className="inline-flex p-4 rounded-2xl bg-gradient-to-br from-primary-500 to-cyan-500 shadow-lg shadow-primary-500/30 mb-4"
            >
              <Shield className="w-8 h-8 text-white" />
            </motion.div>
            <h1 className="text-2xl font-bold text-dark-100">Admin Login</h1>
            <p className="text-dark-400 text-sm mt-1">Access the TempMail Pro control panel</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-4">
            <Input
              type="password"
              label="Admin Password"
              placeholder="Enter admin password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              icon={<Lock className="w-4 h-4" />}
              required
            />
            <Button type="submit" variant="gradient" fullWidth loading={loading}>
              Sign In
            </Button>
          </form>

          <div className="mt-6 p-3 rounded-xl bg-dark-800/50 border border-dark-700">
            <p className="text-xs text-dark-500 flex items-center gap-1">
              <Mail className="w-3 h-3" />
              Default password: admin123 (change in production!)
            </p>
          </div>
        </Card>
      </motion.div>
    </div>
  )
}