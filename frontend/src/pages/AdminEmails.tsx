import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mail,
  Search,
  Trash2,
  RefreshCw,
  User,
} from 'lucide-react'
import { apiClient } from '@/services/api'
import { ADMIN_TOKEN_KEY } from '@/utils/constants'
import { formatDate, cn, debounce } from '@/utils/cn'
import { toast } from 'react-toastify'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Badge from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Skeleton'

interface AdminEmail {
  id: string
  email: string
  local_part: string
  domain: string
  status: string
  expires_at: string
  created_at: string
  emails_count: number
  max_emails: number
  is_custom: boolean
}

export default function AdminEmails() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const adminToken = localStorage.getItem(ADMIN_TOKEN_KEY)

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ['admin-emails', page, search, statusFilter],
    queryFn: async () => {
      const response = await apiClient.get<{
        emails: AdminEmail[]
        total: number
        page: number
        page_size: number
        total_pages: number
      }>('/admin/emails', {
        headers: { 'X-Admin-Token': adminToken || '' },
        params: { page, page_size: 20, search: search || undefined, status: statusFilter === 'all' ? undefined : statusFilter },
      })
      return response
    },
  })

  const deleteMutation = useMutation({
    mutationFn: async (emailId: string) => {
      await apiClient.delete(`/admin/emails/${emailId}`, {
        headers: { 'X-Admin-Token': adminToken || '' },
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-emails'] })
      toast.success('Email address deleted')
    },
    onError: (error: any) => {
      toast.error(error.detail || 'Failed to delete email')
    },
  })

  const handleSearch = debounce((value: string) => {
    setSearch(value)
    setPage(1)
  }, 300)

  const statusColors: Record<string, string> = {
    active: 'badge-success',
    expired: 'badge-warning',
    blocked: 'badge-danger',
    deleted: 'badge-neutral',
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between flex-wrap gap-4"
      >
        <div>
          <h1 className="text-2xl font-bold text-dark-100 mb-1 flex items-center gap-2">
            <Mail className="w-6 h-6 text-primary-400" />
            Email Addresses
          </h1>
          <p className="text-dark-400">Manage all temporary email addresses</p>
        </div>
        <Button variant="ghost" onClick={() => refetch()} loading={isFetching}>
          <RefreshCw className="w-4 h-4" />
          Refresh
        </Button>
      </motion.div>

      <Card glass className="p-4">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <Input
              placeholder="Search by email or username..."
              icon={<Search className="w-4 h-4" />}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-1">
            {['all', 'active', 'expired', 'blocked', 'deleted'].map((status) => (
              <button
                key={status}
                onClick={() => {
                  setStatusFilter(status)
                  setPage(1)
                }}
                className={cn(
                  'px-3 py-2 rounded-xl text-xs font-medium transition-colors',
                  statusFilter === status
                    ? 'bg-primary-500/20 text-primary-300'
                    : 'text-dark-400 hover:text-dark-200'
                )}
              >
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </Card>

      <Card glass className="overflow-hidden">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-16" />
            ))}
          </div>
        ) : data?.emails?.length === 0 ? (
          <div className="p-16 text-center">
            <Mail className="w-12 h-12 text-dark-600 mx-auto mb-4" />
            <p className="text-dark-400">No email addresses found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-dark-800/50 text-dark-400 text-left">
                  <th className="px-4 py-3 font-medium">Email</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Emails</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                  <th className="px-4 py-3 font-medium">Expires</th>
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                <AnimatePresence>
                  {data?.emails?.map((email) => (
                    <motion.tr
                      key={email.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="border-b border-dark-800/30 hover:bg-dark-800/30 transition-colors"
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="p-1.5 rounded-lg bg-dark-800">
                            <User className="w-3.5 h-3.5 text-dark-400" />
                          </div>
                          <div>
                            <p className="text-dark-100 font-medium">{email.email}</p>
                            {email.is_custom && <Badge variant="primary" className="mt-0.5">Custom</Badge>}
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={statusColors[email.status] || 'badge-neutral'}>
                          {email.status}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="text-dark-300">
                          {email.emails_count}/{email.max_emails}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-dark-400">
                        {formatDate(email.created_at)}
                      </td>
                      <td className="px-4 py-3 text-dark-400">
                        {formatDate(email.expires_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => {
                            if (window.confirm(`Delete ${email.email}?`)) {
                              deleteMutation.mutate(email.id)
                            }
                          }}
                          className="p-2 rounded-lg hover:bg-red-500/20 text-dark-400 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </motion.tr>
                  ))}
                </AnimatePresence>
              </tbody>
            </table>
          </div>
        )}

        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between p-4 border-t border-dark-800/50">
            <Button
              variant="ghost"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Previous
            </Button>
            <span className="text-xs text-dark-400">
              Page {page} of {data.total_pages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              disabled={page >= data.total_pages}
              onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
            >
              Next
            </Button>
          </div>
        )}
      </Card>
    </div>
  )
}