import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Copy, KeyRound, Check, ShieldCheck, ExternalLink, Timer, Zap } from 'lucide-react'
import { OTPCode, VerificationLink } from '@/types'
import { copyToClipboard, formatTimer } from '@/utils/cn'
import { toast } from 'react-toastify'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'

interface OTPCardProps {
  otpCodes: OTPCode[]
  verificationLinks: VerificationLink[]
  expiresAt?: string
}

export default function OTPCard({ otpCodes, verificationLinks, expiresAt }: OTPCardProps) {
  const [copiedCode, setCopiedCode] = useState<string | null>(null)
  const [timeRemaining, setTimeRemaining] = useState<number>(0)

  useEffect(() => {
    if (!expiresAt) return
    const interval = setInterval(() => {
      const now = new Date().getTime()
      const expiry = new Date(expiresAt).getTime()
      const remaining = Math.max(0, Math.floor((expiry - now) / 1000))
      setTimeRemaining(remaining)
      if (remaining <= 0) clearInterval(interval)
    }, 1000)
    return () => clearInterval(interval)
  }, [expiresAt])

  const copyOTP = async (code: string) => {
    await copyToClipboard(code)
    setCopiedCode(code)
    toast.success('OTP copied to clipboard')
    setTimeout(() => setCopiedCode(null), 2000)
  }

  if (otpCodes.length === 0 && verificationLinks.length === 0) {
    return null
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="relative overflow-hidden rounded-2xl border border-primary-500/30 bg-gradient-to-br from-primary-500/10 to-cyan-500/5 p-6"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-transparent pointer-events-none" />

      <div className="relative">
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-xl bg-primary-500/20">
            <ShieldCheck className="w-5 h-5 text-primary-400" />
          </div>
          <div>
            <h3 className="font-semibold text-dark-100">Security Codes Detected</h3>
            <p className="text-xs text-dark-400">Automatically extracted from email</p>
          </div>
          {expiresAt && timeRemaining > 0 && (
            <Badge variant="warning" className="ml-auto">
              <Timer className="w-3 h-3" />
              {formatTimer(timeRemaining)}
            </Badge>
          )}
        </div>

        {otpCodes.length > 0 && (
          <div className="space-y-3 mb-4">
            {otpCodes.map((otp, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="flex items-center gap-3 p-3 rounded-xl bg-dark-900/50 border border-dark-700"
              >
                <div className="p-2 rounded-lg bg-primary-500/15">
                  <KeyRound className="w-4 h-4 text-primary-400" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-dark-500 mb-0.5">
                    {otp.length}-digit code
                    {otp.source === 'context' && ' • contextual'}
                  </p>
                  <p className="font-mono text-2xl font-bold text-dark-100 tracking-wider">
                    {otp.code}
                  </p>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => copyOTP(otp.code)}
                  leftIcon={
                    copiedCode === otp.code ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )
                  }
                >
                  {copiedCode === otp.code ? 'Copied' : 'Copy'}
                </Button>
              </motion.div>
            ))}
          </div>
        )}

        {verificationLinks.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs font-medium text-dark-400 flex items-center gap-1">
              <Zap className="w-3 h-3" />
              Verification Links
            </p>
            {verificationLinks.map((link, idx) => (
              <a
                key={idx}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 p-3 rounded-xl bg-dark-900/50 border border-dark-700 hover:border-primary-500/50 transition-colors group"
              >
                <ExternalLink className="w-4 h-4 text-primary-400 flex-shrink-0" />
                <span className="flex-1 text-sm text-dark-300 truncate group-hover:text-primary-300 transition-colors">
                  {link.text}
                </span>
                <span className="text-xs text-dark-500">Open →</span>
              </a>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  )
}