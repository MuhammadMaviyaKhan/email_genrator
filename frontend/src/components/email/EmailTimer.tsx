import { motion } from 'framer-motion'
import { Timer, RefreshCw, AlertTriangle } from 'lucide-react'
import { useState, useEffect } from 'react'
import { getTimeRemaining, formatTimer } from '@/utils/cn'
import { useExtendEmailAddress } from '@/hooks/useApi'
import { toast } from 'react-toastify'
import Button from '@/components/ui/Button'
import { STORAGE_KEYS } from '@/utils/constants'

export default function EmailTimer({ emailId, expiresAt }: { emailId: string; expiresAt: string }) {
  const [timeRemaining, setTimeRemaining] = useState(() => getTimeRemaining(expiresAt))
  const extendMutation = useExtendEmailAddress()

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeRemaining(getTimeRemaining(expiresAt))
    }, 1000)
    return () => clearInterval(interval)
  }, [expiresAt])

  const handleExtend = async () => {
    try {
      await extendMutation.mutateAsync({ id: emailId, hours: 24 })
      const emailData = JSON.parse(localStorage.getItem(STORAGE_KEYS.EMAIL_DATA) || '{}')
      emailData.expires_at = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
      localStorage.setItem(STORAGE_KEYS.EMAIL_DATA, JSON.stringify(emailData))
      toast.success('Email extended for 24 hours')
    } catch (error: any) {
      toast.error(error.detail || 'Failed to extend email')
    }
  }

  if (timeRemaining.expired) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30"
      >
        <AlertTriangle className="w-5 h-5 text-red-400" />
        <div className="flex-1">
          <p className="text-sm font-medium text-red-300">Email Expired</p>
          <p className="text-xs text-red-400/80">This email address is no longer active</p>
        </div>
        <Button variant="danger" size="sm" onClick={handleExtend} loading={extendMutation.isPending}>
          <RefreshCw className="w-4 h-4" />
          Renew
        </Button>
      </motion.div>
    )
  }

  const totalSeconds = timeRemaining.hours * 3600 + timeRemaining.minutes * 60 + timeRemaining.seconds
  const progress = Math.min(100, (totalSeconds / (24 * 3600)) * 100)

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3 p-4 rounded-xl bg-dark-900/50 border border-dark-700"
    >
      <div className="relative">
        <svg className="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="rgb(59 130 246 / 0.2)"
            strokeWidth="3"
          />
          <path
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
            fill="none"
            stroke="rgb(59 130 246)"
            strokeWidth="3"
            strokeDasharray={`${progress}, 100`}
            strokeLinecap="round"
          />
        </svg>
        <Timer className="w-4 h-4 text-primary-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
      </div>

      <div className="flex-1">
        <p className="text-xs text-dark-400 mb-0.5">Expires in</p>
        <p className="font-mono text-xl font-bold text-dark-100 tabular-nums">
          {formatTimer(totalSeconds)}
        </p>
      </div>

      <Button variant="secondary" size="sm" onClick={handleExtend} loading={extendMutation.isPending}>
        <RefreshCw className="w-4 h-4" />
        Extend
      </Button>
    </motion.div>
  )
}
