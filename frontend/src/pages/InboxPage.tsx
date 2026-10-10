import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Mail, ArrowLeft, RefreshCw } from 'lucide-react'
import { useEmailAddress, useEmailDetail, useDeleteEmail } from '@/hooks/useApi'
import { useWebSocket } from '@/hooks/useWebSocket'
import { STORAGE_KEYS } from '@/utils/constants'
import { copyToClipboard } from '@/utils/cn'
import { toast } from 'react-toastify'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Inbox from '@/components/email/Inbox'
import EmailViewer from '@/components/email/EmailViewer'
import EmailTimer from '@/components/email/EmailTimer'
import { Skeleton } from '@/components/ui/Skeleton'

export default function InboxPage() {
  const { emailId } = useParams<{ emailId: string }>()
  const navigate = useNavigate()
  const [selectedMessage, setSelectedMessage] = useState<string | null>(null)
  const [emailData, setEmailData] = useState<any>(null)

  const token = localStorage.getItem(STORAGE_KEYS.TOKEN)
  const storedEmail = localStorage.getItem(STORAGE_KEYS.EMAIL_DATA)
    ? JSON.parse(localStorage.getItem(STORAGE_KEYS.EMAIL_DATA) || '{}')
    : null

  const effectiveEmailId = emailId || storedEmail?.id

  const { data: emailAddress, isLoading } = useEmailAddress(effectiveEmailId || '')
  const { data: emailDetail, refetch: refetchEmail } = useEmailDetail(
    effectiveEmailId || '',
    selectedMessage || ''
  )
  const deleteMutation = useDeleteEmail()

  useEffect(() => {
    if (emailAddress) {
      setEmailData(emailAddress)
      localStorage.setItem(STORAGE_KEYS.EMAIL_DATA, JSON.stringify(emailAddress))
    }
  }, [emailAddress])

  const { isConnected, lastMessage } = useWebSocket({
    emailId: effectiveEmailId,
    token,
    onMessage: (message) => {
      if (message.type === 'new_email') {
        toast.info(`New email from ${message.data.from_address}`)
      }
    },
  })

  useEffect(() => {
    if (lastMessage?.type === 'new_email' && effectiveEmailId) {
      // Handled by Inbox component
    }
  }, [lastMessage])

  const handleDelete = async (id: string) => {
    try {
      await deleteMutation.mutateAsync({ emailId: effectiveEmailId!, messageId: id })
      setSelectedMessage(null)
      refetchEmail()
      toast.success('Email deleted')
    } catch (error: any) {
      toast.error(error.detail || 'Failed to delete email')
    }
  }

  const handleCopyEmail = async () => {
    if (emailData?.email) {
      await copyToClipboard(emailData.email)
      toast.success('Email copied to clipboard')
    }
  }

  if (isLoading || !emailData) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-96" />
          <Skeleton className="h-96" />
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-6 flex items-center justify-between flex-wrap gap-4"
      >
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/generate')}
            className="p-2 rounded-xl bg-dark-800 hover:bg-dark-700 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-dark-300" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-dark-100 flex items-center gap-2">
              <Mail className="w-6 h-6 text-primary-400" />
              Inbox
            </h1>
            <button
              onClick={handleCopyEmail}
              className="text-sm text-primary-400 hover:text-primary-300 transition-colors"
            >
              {emailData.email}
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {isConnected ? (
            <span className="flex items-center gap-1 text-xs text-green-400 bg-green-500/10 px-3 py-1.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
              Live
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-red-400 bg-red-500/10 px-3 py-1.5 rounded-full">
              <span className="w-2 h-2 rounded-full bg-red-400" />
              Offline
            </span>
          )}
        </div>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5">
          <Card glass className="p-4 h-[calc(100vh-200px)] overflow-hidden flex flex-col">
            <Inbox emailId={effectiveEmailId!} />
          </Card>
        </div>

        <div className="lg:col-span-7 space-y-4">
          <EmailTimer emailId={effectiveEmailId!} expiresAt={emailData.expires_at} />

          <Card glass className="p-4 h-[calc(100vh-280px)] overflow-y-auto no-scrollbar">
            <AnimatePresence mode="wait">
              {selectedMessage ? (
                emailDetail ? (
                  <motion.div
                    key={selectedMessage}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                  >
                    <EmailViewer
                      email={emailDetail}
                      otpData={{
                        otp_codes: emailDetail.otp_codes || [],
                        verification_links: emailDetail.verification_links || [],
                      }}
                    />
                    <div className="mt-4 flex gap-2">
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(selectedMessage)}
                      >
                        Delete Email
                      </Button>
                    </div>
                  </motion.div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <RefreshCw className="w-8 h-8 animate-spin text-dark-500" />
                  </div>
                )
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center h-full text-center"
                >
                  <Mail className="w-16 h-16 text-dark-600 mb-4" />
                  <p className="text-dark-400">Select an email to view its content</p>
                </motion.div>
              )}
            </AnimatePresence>
          </Card>
        </div>
      </div>
    </div>
  )
}