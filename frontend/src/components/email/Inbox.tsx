import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Search, Trash2, RefreshCw, Inbox as InboxIcon, Wifi, WifiOff } from 'lucide-react'
import { useInbox, useDeleteAllEmails } from '@/hooks/useApi'
import { useWebSocket } from '@/hooks/useWebSocket'
import { Email } from '@/types'
import { cn, debounce } from '@/utils/cn'
import { STORAGE_KEYS } from '@/utils/constants'
import { toast } from 'react-toastify'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Badge from '@/components/ui/Badge'
import { SkeletonEmail } from '@/components/ui/Skeleton'
import EmailCard from './EmailCard'
import EmptyState from '@/components/common/EmptyState'

interface InboxProps {
  emailId: string
}

export default function Inbox({ emailId }: InboxProps) {
  const navigate = useNavigate()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [emails, setEmails] = useState<Email[]>([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [selectedEmail, setSelectedEmail] = useState<string | null>(null)

  const token = localStorage.getItem(STORAGE_KEYS.TOKEN)

  const { data, isLoading, isFetching, refetch } = useInbox(
    emailId,
    page,
    20,
    statusFilter,
    search || undefined
  )

  const deleteAllMutation = useDeleteAllEmails()

  useEffect(() => {
    if (data) {
      setEmails(data.emails)
      setTotal(data.total)
      setTotalPages(data.total_pages)
      if (!selectedEmail && data.emails.length > 0) {
        setSelectedEmail(data.emails[0].id)
      }
    }
  }, [data, selectedEmail])

  const handleSearch = useCallback(
    debounce((value: string) => {
      setSearch(value)
      setPage(1)
    }, 300),
    []
  )

  const { isConnected } = useWebSocket({
    emailId,
    token,
    onMessage: (message) => {
      if (message.type === 'new_email') {
        toast.info(`New email from ${message.data.from_address}`)
        refetch()
      } else if (message.type === 'email_deleted') {
        refetch()
      } else if (message.type === 'email_status_changed') {
        refetch()
      }
    },
  })

  const handleDeleteAll = async () => {
    if (window.confirm('Are you sure you want to delete all emails?')) {
      try {
        await deleteAllMutation.mutateAsync(emailId)
        setSelectedEmail(null)
        toast.success('All emails deleted')
        refetch()
      } catch (error: any) {
        toast.error(error.detail || 'Failed to delete emails')
      }
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between gap-4 mb-4 flex-wrap">
        <div className="flex items-center gap-3">
          <h2 className="text-lg font-semibold text-dark-100 flex items-center gap-2">
            <InboxIcon className="w-5 h-5 text-primary-400" />
            Inbox
          </h2>
          <Badge variant="primary" dot>
            {total} emails
          </Badge>
          {isConnected ? (
            <span className="flex items-center gap-1 text-xs text-green-400">
              <Wifi className="w-3 h-3" />
              Live
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-red-400">
              <WifiOff className="w-3 h-3" />
              Offline
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetch()}
            loading={isFetching}
          >
            <RefreshCw className="w-4 h-4" />
          </Button>
          <Button variant="danger" size="sm" onClick={handleDeleteAll}>
            <Trash2 className="w-4 h-4" />
            Delete All
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <div className="flex-1">
          <Input
            placeholder="Search emails..."
            icon={<Search className="w-4 h-4" />}
            onChange={(e) => handleSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-1">
          {['all', 'received', 'read'].map((status) => (
            <button
              key={status}
              onClick={() => {
                setStatusFilter(status === 'all' ? undefined : status)
                setPage(1)
              }}
              className={cn(
                'px-3 py-2 rounded-xl text-xs font-medium transition-colors',
                (statusFilter || 'all') === status
                  ? 'bg-primary-500/20 text-primary-300'
                  : 'text-dark-400 hover:text-dark-200'
              )}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto no-scrollbar min-h-[400px]">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonEmail key={i} />
            ))}
          </div>
        ) : emails.length === 0 ? (
          <EmptyState
            icon={<InboxIcon className="w-12 h-12" />}
            title="No emails yet"
            description="Your inbox is empty. New emails will appear here automatically."
          />
        ) : (
          <AnimatePresence>
            <div className="space-y-2">
              {emails.map((email) => (
                <EmailCard
                  key={email.id}
                  email={email}
                  selected={selectedEmail === email.id}
                  onClick={() => {
                    setSelectedEmail(email.id)
                    navigate(`/email/${emailId}/${email.id}`)
                  }}
                />
              ))}
            </div>
          </AnimatePresence>
        )}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-dark-800/50">
          <Button
            variant="ghost"
            size="sm"
            disabled={page <= 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="text-xs text-dark-400">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="ghost"
            size="sm"
            disabled={page >= totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  )
}