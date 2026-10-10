import { motion } from 'framer-motion'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/services/api'
import { ADMIN_TOKEN_KEY } from '@/utils/constants'
import {
  Mail,
  Users,
  Activity,
  Server,
  TrendingUp,
  Clock,
  Database,
  ShieldAlert,
} from 'lucide-react'
import Card from '@/components/ui/Card'
import { Skeleton } from '@/components/ui/Skeleton'

interface AdminStats {
  total_addresses: number
  active_addresses: number
  expired_addresses: number
  total_emails: number
  emails_today: number
  emails_this_week: number
  emails_this_month: number
  active_domains: number
  total_domains: number
  system_status: {
    database: string
    redis: string
    smtp: string
    uptime: number
  }
}

export default function AdminDashboard() {
  const adminToken = localStorage.getItem(ADMIN_TOKEN_KEY)

  const { data: stats, isLoading } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const response = await apiClient.get<AdminStats>('/admin/stats', {
        headers: { 'X-Admin-Token': adminToken || '' },
      })
      return response
    },
    refetchInterval: 5000,
  })

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    )
  }

  const statCards = [
    { label: 'Total Addresses', value: stats?.total_addresses || 0, icon: Users, color: 'from-blue-500 to-blue-600' },
    { label: 'Active Addresses', value: stats?.active_addresses || 0, icon: Activity, color: 'from-green-500 to-green-600' },
    { label: 'Total Emails', value: stats?.total_emails || 0, icon: Mail, color: 'from-purple-500 to-purple-600' },
    { label: 'Emails Today', value: stats?.emails_today || 0, icon: TrendingUp, color: 'from-cyan-500 to-cyan-600' },
    { label: 'This Week', value: stats?.emails_this_week || 0, icon: Clock, color: 'from-orange-500 to-orange-600' },
    { label: 'This Month', value: stats?.emails_this_month || 0, icon: Database, color: 'from-pink-500 to-pink-600' },
    { label: 'Active Domains', value: stats?.active_domains || 0, icon: Server, color: 'from-indigo-500 to-indigo-600' },
    { label: 'Expired', value: stats?.expired_addresses || 0, icon: ShieldAlert, color: 'from-red-500 to-red-600' },
  ]

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-2xl font-bold text-dark-100 mb-1">Dashboard</h1>
        <p className="text-dark-400">System overview and statistics</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, idx) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
          >
            <Card hover glass className="p-6 relative overflow-hidden">
              <div className={`absolute top-0 right-0 w-20 h-20 bg-gradient-to-br ${stat.color} opacity-10 rounded-bl-3xl`} />
              <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${stat.color} mb-4`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
              <p className="text-3xl font-bold text-dark-100 mb-1">{stat.value.toLocaleString()}</p>
              <p className="text-sm text-dark-400">{stat.label}</p>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card glass className="p-6">
          <h3 className="font-semibold text-dark-100 mb-4 flex items-center gap-2">
            <Server className="w-5 h-5 text-primary-400" />
            System Status
          </h3>
          <div className="space-y-3">
            {[
              { label: 'Database', status: stats?.system_status?.database || 'unknown', ok: stats?.system_status?.database === 'healthy' },
              { label: 'Redis Cache', status: stats?.system_status?.redis || 'unknown', ok: stats?.system_status?.redis === 'healthy' },
              { label: 'SMTP Server', status: stats?.system_status?.smtp || 'unknown', ok: stats?.system_status?.smtp === 'healthy' },
            ].map((item) => (
              <div key={item.label} className="flex items-center justify-between p-3 rounded-xl bg-dark-900/50 border border-dark-800">
                <span className="text-dark-300 text-sm">{item.label}</span>
                <span className={`flex items-center gap-2 text-sm ${item.ok ? 'text-green-400' : 'text-yellow-400'}`}>
                  <span className={`w-2 h-2 rounded-full ${item.ok ? 'bg-green-400' : 'bg-yellow-400'} animate-pulse`} />
                  {item.status}
                </span>
              </div>
            ))}
            <div className="flex items-center justify-between p-3 rounded-xl bg-dark-900/50 border border-dark-800">
              <span className="text-dark-300 text-sm">Uptime</span>
              <span className="text-dark-200 text-sm">
                {Math.floor((stats?.system_status?.uptime || 0) / 3600)}h {Math.floor(((stats?.system_status?.uptime || 0) % 3600) / 60)}m
              </span>
            </div>
          </div>
        </Card>

        <Card glass className="p-6">
          <h3 className="font-semibold text-dark-100 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-400" />
            Email Volume
          </h3>
          <div className="space-y-4">
            {[
              { label: 'Today', value: stats?.emails_today || 0, max: Math.max(stats?.emails_today || 1, 1) },
              { label: 'This Week', value: stats?.emails_this_week || 0, max: Math.max(stats?.emails_this_week || 1, 1) },
              { label: 'This Month', value: stats?.emails_this_month || 0, max: Math.max(stats?.emails_this_month || 1, stats?.emails_today || 1) },
            ].map((item) => (
              <div key={item.label}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-dark-400">{item.label}</span>
                  <span className="text-sm font-medium text-dark-200">{item.value}</span>
                </div>
                <div className="h-2 rounded-full bg-dark-800 overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${(item.value / item.max) * 100}%` }}
                    transition={{ duration: 0.8, ease: 'easeOut' }}
                    className="h-full bg-gradient-to-r from-primary-500 to-cyan-500"
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}