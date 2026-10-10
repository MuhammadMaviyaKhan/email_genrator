import { useState } from 'react'
import { motion } from 'framer-motion'
import { Mail, Copy, RefreshCw, Check, Sparkles, Shield, Zap, Globe, Clock } from 'lucide-react'
import { useGenerateEmail, useCreateCustomEmail, useDomains } from '@/hooks/useApi'
import { apiClient } from '@/services/api'
import { STORAGE_KEYS } from '@/utils/constants'
import { toast } from 'react-toastify'
import { copyToClipboard } from '@/utils/cn'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'

const TTL_OPTIONS = [
  { label: '10 min', minutes: 10 },
  { label: '1 hour', minutes: 60 },
  { label: '24 hours', minutes: 1440 },
  { label: '7 days', minutes: 10080 },
]

export default function GenerateEmail() {
  const [localPart, setLocalPart] = useState('')
  const [selectedDomain, setSelectedDomain] = useState<string>('')
  const [ttl, setTtl] = useState(1440)
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState<'random' | 'custom'>('random')

  const generateMutation = useGenerateEmail()
  const customMutation = useCreateCustomEmail()
  const { data: domains } = useDomains()

  const handleGenerate = async () => {
    try {
      const result = await generateMutation.mutateAsync({
        count: 1,
        domain: selectedDomain || undefined,
        ttl_hours: Math.floor(ttl / 60),
      })

      const emailData = result.email
      localStorage.setItem(STORAGE_KEYS.TOKEN, result.token)
      localStorage.setItem(STORAGE_KEYS.EMAIL_ID, emailData.id)
      localStorage.setItem(STORAGE_KEYS.EMAIL_DATA, JSON.stringify(emailData))

      apiClient.setToken(result.token)
      toast.success('Email address generated!')
    } catch (error: any) {
      toast.error(error.detail || 'Failed to generate email')
    }
  }

  const handleCreateCustom = async () => {
    if (!localPart) {
      toast.error('Please enter a username')
      return
    }

    try {
      const result = await customMutation.mutateAsync({
        local_part: localPart,
        domain: selectedDomain,
      })

      localStorage.setItem(STORAGE_KEYS.EMAIL_ID, result.id)
      localStorage.setItem(STORAGE_KEYS.EMAIL_DATA, JSON.stringify(result))

      toast.success('Custom email created!')
    } catch (error: any) {
      toast.error(error.detail || 'Failed to create email')
    }
  }

  const copyEmail = async (email: string) => {
    await copyToClipboard(email)
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }

  const currentEmail = localStorage.getItem(STORAGE_KEYS.EMAIL_DATA)
    ? JSON.parse(localStorage.getItem(STORAGE_KEYS.EMAIL_DATA) || '{}')
    : null

  return (
    <div className="space-y-6">
      <Card glass className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-primary-500 to-cyan-500 shadow-lg shadow-primary-500/30">
            <Mail className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-dark-100">Create Temporary Email</h2>
            <p className="text-sm text-dark-400">Generate a secure disposable email address</p>
          </div>
        </div>

        <div className="flex gap-1 mb-6 p-1 rounded-xl bg-dark-900/50 border border-dark-800">
          {(['random', 'custom'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab
                  ? 'bg-primary-500 text-white shadow-lg shadow-primary-500/25'
                  : 'text-dark-400 hover:text-dark-200'
              }`}
            >
              {tab === 'random' ? 'Random' : 'Custom'}
            </button>
          ))}
        </div>

        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          {activeTab === 'random' ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-dark-300 mb-1.5 block">Domain</label>
                <select
                  value={selectedDomain}
                  onChange={(e) => setSelectedDomain(e.target.value)}
                  className="input"
                >
                  <option value="">Random domain</option>
                  {domains?.map((d) => (
                    <option key={d.domain} value={d.domain}>
                      {d.domain}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-dark-300 mb-1.5 block">Expiration</label>
                <div className="flex gap-1">
                  {TTL_OPTIONS.map((opt) => (
                    <button
                      key={opt.minutes}
                      onClick={() => setTtl(opt.minutes)}
                      className={`flex-1 py-2 px-2 rounded-lg text-xs font-medium transition-all ${
                        ttl === opt.minutes
                          ? 'bg-primary-500/20 text-primary-300 border border-primary-500/30'
                          : 'bg-dark-800/50 text-dark-400 hover:text-dark-200'
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex gap-2">
                <div className="flex-1">
                  <Input
                    placeholder="username"
                    value={localPart}
                    onChange={(e) => setLocalPart(e.target.value.toLowerCase().replace(/[^a-z0-9._-]/g, ''))}
                    icon={<Sparkles className="w-4 h-4" />}
                  />
                </div>
                <div className="flex items-center px-3 rounded-xl bg-dark-800/50 border border-dark-700 text-dark-400 text-sm">
                  @{selectedDomain || (domains?.[0]?.domain ?? 'domain')}
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-dark-300 mb-1.5 block">Domain</label>
                <select
                  value={selectedDomain}
                  onChange={(e) => setSelectedDomain(e.target.value)}
                  className="input"
                >
                  {domains?.map((d) => (
                    <option key={d.domain} value={d.domain}>
                      {d.domain}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          <Button
            variant="gradient"
            size="lg"
            fullWidth
            onClick={activeTab === 'random' ? handleGenerate : handleCreateCustom}
            loading={generateMutation.isPending || customMutation.isPending}
            leftIcon={<Zap className="w-5 h-5" />}
          >
            {activeTab === 'random' ? 'Generate Email' : 'Create Custom Email'}
          </Button>
        </motion.div>
      </Card>

      {currentEmail?.email && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card glass glow className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-dark-100 flex items-center gap-2">
                <Shield className="w-4 h-4 text-primary-400" />
                Your Active Email
              </h3>
              <Badge variant="success" dot>
                Active
              </Badge>
            </div>

            <div className="flex items-center gap-3 p-4 rounded-xl bg-dark-900/50 border border-dark-700">
              <div className="flex-1 min-w-0">
                <p className="font-mono text-lg text-dark-100 truncate">{currentEmail.email}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-dark-500">
                  <Clock className="w-3 h-3" />
                  Expires: {new Date(currentEmail.expires_at).toLocaleString()}
                </div>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => copyEmail(currentEmail.email)}
              >
                {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                {copied ? 'Copied' : 'Copy'}
              </Button>
            </div>

            <div className="grid grid-cols-3 gap-3 mt-4">
              <div className="p-3 rounded-xl bg-dark-900/50 border border-dark-800 text-center">
                <Globe className="w-4 h-4 text-primary-400 mx-auto mb-1" />
                <p className="text-xs text-dark-400">Domain</p>
                <p className="text-xs font-medium text-dark-200 truncate">{currentEmail.domain}</p>
              </div>
              <div className="p-3 rounded-xl bg-dark-900/50 border border-dark-800 text-center">
                <Mail className="w-4 h-4 text-primary-400 mx-auto mb-1" />
                <p className="text-xs text-dark-400">Emails</p>
                <p className="text-xs font-medium text-dark-200">{currentEmail.emails_count}</p>
              </div>
              <div className="p-3 rounded-xl bg-dark-900/50 border border-dark-800 text-center">
                <RefreshCw className="w-4 h-4 text-primary-400 mx-auto mb-1" />
                <p className="text-xs text-dark-400">Actions</p>
                <button
                  onClick={handleGenerate}
                  className="text-xs font-medium text-primary-400 hover:text-primary-300"
                >
                  Renew
                </button>
              </div>
            </div>
          </Card>
        </motion.div>
      )}
    </div>
  )
}