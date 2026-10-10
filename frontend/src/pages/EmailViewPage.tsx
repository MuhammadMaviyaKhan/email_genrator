import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Mail, RefreshCw } from 'lucide-react'
import { useEmailDetail } from '@/hooks/useApi'
import { useWebSocket } from '@/hooks/useWebSocket'
import { STORAGE_KEYS } from '@/utils/constants'
import Button from '@/components/ui/Button'
import EmailViewer from '@/components/email/EmailViewer'
import EmailTimer from '@/components/email/EmailTimer'
import { Skeleton } from '@/components/ui/Skeleton'

export default function EmailViewPage() {
  const { emailId, messageId } = useParams<{ emailId: string; messageId: string }>()
  const navigate = useNavigate()

  const token = localStorage.getItem(STORAGE_KEYS.TOKEN)
  const storedEmail = localStorage.getItem(STORAGE_KEYS.EMAIL_DATA)
    ? JSON.parse(localStorage.getItem(STORAGE_KEYS.EMAIL_DATA) || '{}')
    : null

  const effectiveEmailId = emailId || storedEmail?.id
  const { data: email, isLoading, refetch } = useEmailDetail(effectiveEmailId || '', messageId || '')

  useWebSocket({
    emailId: effectiveEmailId,
    token,
    onMessage: (message) => {
      if (message.type === 'email_status_changed' || message.type === 'new_email') {
        refetch()
      }
    },
  })

  useEffect(() => {
    if (email) {
      refetch()
    }
  }, [messageId])

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Skeleton className="h-8 w-48 mb-6" />
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (!email) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <Mail className="w-16 h-16 text-dark-600 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-dark-200 mb-2">Email not found</h2>
        <Button onClick={() => navigate('/inbox')} leftIcon={<ArrowLeft className="w-4 h-4" />}>
          Back to Inbox
        </Button>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <button
          onClick={() => navigate('/inbox')}
          className="p-2 rounded-xl bg-dark-800 hover:bg-dark-700 transition-colors"
        >
          <ArrowLeft className="w-5 h-5 text-dark-300" />
        </button>
        <Button variant="ghost" size="sm" onClick={() => refetch()} leftIcon={<RefreshCw className="w-4 h-4" />}>
          Refresh
        </Button>
      </div>

      <div className="space-y-4">
        <EmailTimer emailId={effectiveEmailId!} expiresAt={storedEmail?.expires_at || email.received_at} />
        <EmailViewer
          email={email}
          otpData={{
            otp_codes: email.otp_codes || [],
            verification_links: email.verification_links || [],
          }}
        />
      </div>
    </div>
  )
}