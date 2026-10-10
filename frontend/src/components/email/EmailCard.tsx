import { motion } from 'framer-motion'
import { Paperclip, AlertCircle, CheckCircle2 } from 'lucide-react'
import { Email } from '@/types'
import { cn, formatRelativeTime, getInitials } from '@/utils/cn'
import Badge from '@/components/ui/Badge'

interface EmailCardProps {
  email: Email
  onClick: () => void
  selected?: boolean
}

export default function EmailCard({ email, onClick, selected }: EmailCardProps) {
  const hasAttachments = email.attachments && email.attachments.length > 0
  const isUnread = email.status === 'received'

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      whileHover={{ scale: 1.01 }}
      onClick={onClick}
      className={cn(
        'flex items-start gap-4 p-4 rounded-xl cursor-pointer transition-all border',
        selected
          ? 'bg-primary-500/10 border-primary-500/30'
          : isUnread
          ? 'bg-dark-800/50 border-dark-700 hover:border-primary-500/50'
          : 'bg-dark-900/30 border-dark-800/50 hover:border-dark-700',
        'hover:bg-dark-800/50'
      )}
    >
      <div
        className={cn(
          'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold',
          isUnread ? 'bg-primary-500/20 text-primary-300' : 'bg-dark-800 text-dark-400'
        )}
      >
        {getInitials(email.from_name || email.from_address.split('@')[0])}
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <p className={cn('text-sm font-medium truncate', isUnread ? 'text-dark-100' : 'text-dark-300')}>
            {email.from_name || email.from_address}
          </p>
          <span className="text-xs text-dark-500 flex-shrink-0">
            {formatRelativeTime(email.received_at)}
          </span>
        </div>

        <p className={cn('text-sm mt-0.5 truncate', isUnread ? 'text-dark-200' : 'text-dark-400')}>
          {email.subject || '(No subject)'}
        </p>

        <p className="text-xs text-dark-500 mt-1 line-clamp-1">
          {email.text_body?.substring(0, 100) || email.html_body?.replace(/<[^>]*>/g, '').substring(0, 100) || 'No preview available'}
        </p>

        <div className="flex items-center gap-2 mt-2">
          {isUnread && <Badge variant="primary" dot>New</Badge>}
          {hasAttachments && (
            <span className="flex items-center gap-1 text-xs text-dark-500">
              <Paperclip className="w-3 h-3" />
              {email.attachments!.length}
            </span>
          )}
          {email.is_spam && (
            <Badge variant="warning">
              <AlertCircle className="w-3 h-3" />
              Spam
            </Badge>
          )}
          {email.status === 'read' && (
            <span className="flex items-center gap-1 text-xs text-dark-600">
              <CheckCircle2 className="w-3 h-3" />
              Read
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}