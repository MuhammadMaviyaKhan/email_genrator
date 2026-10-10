import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  FileText,
  Search,
  AlertCircle,
  Info,
  AlertTriangle,
  CheckCircle,
  Download,
} from 'lucide-react'
import { apiClient } from '@/services/api'
import { ADMIN_TOKEN_KEY } from '@/utils/constants'
import { formatDate, cn, debounce } from '@/utils/cn'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { Skeleton } from '@/components/ui/Skeleton'

interface LogEntry {
  id: string
  level: string
  event_type: string
  message: string
  details: Record<string, any> | null
  ip_address: string | null
  created_at: string
}

const levelConfig: Record<string, { icon: any; color: string; bg: string }> = {
  INFO: { icon: Info, color: 'text-blue-400', bg: 'bg-blue-500/10' },
  WARNING: { icon: AlertTriangle, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
  ERROR: { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/10' },
  SUCCESS: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10' },
}

export default function AdminLogs() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [levelFilter, setLevelFilter] = useState<string>('all')
  const adminToken = localStorage.getItem(ADMIN_TOKEN_KEY)

  const { data, isLoading } = useQuery({
    queryKey: ['admin-logs', page, search, levelFilter],
    queryFn: async () => {
      const response = await apiClient.get<{
        logs: LogEntry[]
        total: number
        page: number
        page_size: number
        total_pages: number
      }>('/admin/logs', {
        headers: { 'X-Admin-Token': adminToken || '' },
        params: {
          page,
          page_size: 50,
          search: search || undefined,
          level: levelFilter === 'all' ? undefined : levelFilter,
        },
      })
      return response
    },
    refetchInterval: 10000,
  })

  const handleSearch = debounce((value: string) => {
    setSearch(value)
    setPage(1)
  }, 300)

  const handleExport = async () => {
    try {
      const response = await apiClient.get('/admin/logs/export', {
        headers: { 'X-Admin-Token': adminToken || '' },
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response as BlobPart]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `logs-${new Date().toISOString().split('T')[0]}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Export failed:', error)
    }
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
            <FileText className="w-6 h-6 text-primary-400" />
            System Logs
          </h1>
          <p className="text-dark-400">View and monitor system activity</p>
        </div>
        <Button variant="secondary" onClick={handleExport} leftIcon={<Download className="w-4 h-4" />}>
          Export
        </Button>
      </motion.div>

      <Card glass className="p-4">
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex-1 min-w-[200px]">
            <Input
              placeholder="Search logs..."
              icon={<Search className="w-4 h-4" />}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-1">
            {['all', 'INFO', 'WARNING', 'ERROR', 'SUCCESS'].map((level) => (
              <button
                key={level}
                onClick={() => {
                  setLevelFilter(level)
                  setPage(1)
                }}
                className={cn(
                  'px-3 py-2 rounded-xl text-xs font-medium transition-colors',
                  levelFilter === level
                    ? 'bg-primary-500/20 text-primary-300'
                    : 'text-dark-400 hover:text-dark-200'
                )}
              >
                {level}
              </button>
            ))}
          </div>
        </div>
      </Card>

      <Card glass className="overflow-hidden">
        {isLoading ? (
          <div className="p-4 space-y-3">
            {Array.from({ length: 10 }).map((_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </div>
        ) : data?.logs?.length === 0 ? (
          <div className="p-16 text-center">
            <FileText className="w-12 h-12 text-dark-600 mx-auto mb-4" />
            <p className="text-dark-400">No logs found</p>
          </div>
        ) : (
          <div className="divide-y divide-dark-800/30">
            {data?.logs?.map((log, idx) => {
              const config = levelConfig[log.level] || levelConfig.INFO
              const Icon = config.icon
              return (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.02 }}
                  className="flex items-start gap-3 p-4 hover:bg-dark-800/30 transition-colors"
                >
                  <div className={cn('p-2 rounded-lg flex-shrink-0', config.bg)}>
                    <Icon className={cn('w-4 h-4', config.color)} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={cn('text-xs font-semibold uppercase', config.color)}>
                        {log.level}
                      </span>
                      <span className="text-xs text-dark-500 font-mono">{log.event_type}</span>
                      <span className="text-xs text-dark-500 ml-auto">
                        {formatDate(log.created_at)}
                      </span>
                    </div>
                    <p className="text-sm text-dark-200 mt-1">{log.message}</p>
                    {log.ip_address && (
                      <p className="text-xs text-dark-500 mt-1 font-mono">IP: {log.ip_address}</p>
                    )}
                    {log.details && (
                      <pre className="text-xs text-dark-400 mt-2 p-2 rounded-lg bg-dark-900/50 overflow-x-auto">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}
      </Card>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between">
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
    </div>
  )
}