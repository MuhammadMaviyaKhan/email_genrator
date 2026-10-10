import { motion } from 'framer-motion'
import { User, AtSign, Calendar, Paperclip, Download, FileText, Image as ImageIcon } from 'lucide-react'
import { Email } from '@/types'
import { formatDate, formatBytes } from '@/utils/cn'
import Card from '@/components/ui/Card'
import Badge from '@/components/ui/Badge'
import OTPCard from './OTPCard'

interface EmailViewerProps {
  email: Email
  otpData?: {
    otp_codes: any[]
    verification_links: any[]
  }
}

export default function EmailViewer({ email, otpData }: EmailViewerProps) {
  const renderBody = () => {
    if (email.html_body) {
      return (
        <div
          className="prose prose-invert max-w-none break-words"
          dangerouslySetInnerHTML={{ __html: sanitizeHtml(email.html_body) }}
        />
      )
    }
    return (
      <pre className="whitespace-pre-wrap break-words font-sans text-sm text-dark-200 leading-relaxed">
        {email.text_body}
      </pre>
    )
  }

  return (
    <div className="space-y-4">
      <Card glass className="p-6">
        <div className="flex items-start justify-between gap-4 mb-6">
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-dark-100 mb-2">
              {email.subject || '(No subject)'}
            </h1>
            <div className="flex flex-wrap gap-4 text-sm text-dark-400">
              <div className="flex items-center gap-2">
                <User className="w-4 h-4" />
                <span className="truncate">
                  {email.from_name ? `${email.from_name} <${email.from_address}>` : email.from_address}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <AtSign className="w-4 h-4" />
                <span className="truncate">{email.to_addresses?.[0] || 'Unknown'}</span>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                <span>{formatDate(email.received_at)}</span>
              </div>
            </div>
          </div>
          <Badge variant={email.status === 'received' ? 'primary' : 'neutral'} dot>
            {email.status}
          </Badge>
        </div>

        <div className="border-t border-dark-800/50 pt-4">
          {renderBody()}
        </div>

        {email.attachments && email.attachments.length > 0 && (
          <div className="mt-6 border-t border-dark-800/50 pt-4">
            <h3 className="text-sm font-semibold text-dark-200 flex items-center gap-2 mb-3">
              <Paperclip className="w-4 h-4" />
              Attachments ({email.attachments.length})
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {email.attachments.map((att, idx) => (
                <motion.div
                  key={idx}
                  whileHover={{ scale: 1.02 }}
                  className="flex items-center gap-3 p-3 rounded-xl bg-dark-900/50 border border-dark-700 hover:border-primary-500/30 transition-colors"
                >
                  <div className="p-2 rounded-lg bg-dark-800">
                    {att.content_type.startsWith('image/') ? (
                      <ImageIcon className="w-4 h-4 text-primary-400" />
                    ) : (
                      <FileText className="w-4 h-4 text-dark-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-dark-200 truncate">{att.filename}</p>
                    <p className="text-xs text-dark-500">{formatBytes(att.size)}</p>
                  </div>
                  {att.download_url && (
                    <a
                      href={att.download_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 rounded-lg hover:bg-dark-800 transition-colors"
                    >
                      <Download className="w-4 h-4 text-primary-400" />
                    </a>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </Card>

      {((otpData?.otp_codes?.length ?? 0) > 0 || (otpData?.verification_links?.length ?? 0) > 0) && (
        <OTPCard
          otpCodes={otpData?.otp_codes ?? []}
          verificationLinks={otpData?.verification_links ?? []}
        />
      )}
    </div>
  )
}

function sanitizeHtml(html: string): string {
  const allowedTags = ['A', 'B', 'I', 'EM', 'STRONG', 'P', 'BR', 'DIV', 'SPAN', 'UL', 'OL', 'LI', 'TABLE', 'TR', 'TD', 'TH', 'IMG', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'HR', 'SMALL', 'CODE', 'PRE', 'BLOCKQUOTE']
  const allowedAttrs: Record<string, string[]> = {
    A: ['href', 'title', 'target', 'rel'],
    IMG: ['src', 'alt', 'width', 'height'],
    '*': ['style', 'class'],
  }

  const parser = new DOMParser()
  const doc = parser.parseFromString(html, 'text/html')

  function sanitizeNode(node: Element) {
    const children = Array.from(node.children)
    for (const child of children) {
      const tagName = child.tagName
      if (!allowedTags.includes(tagName)) {
        child.replaceWith(...Array.from(child.childNodes))
        continue
      }

      const allowed = allowedAttrs[tagName] || allowedAttrs['*']
      for (const attr of Array.from(child.attributes)) {
        if (!allowed.includes(attr.name)) {
          child.removeAttribute(attr.name)
        }
      }

      if (tagName === 'A') {
        child.setAttribute('target', '_blank')
        child.setAttribute('rel', 'noopener noreferrer')
      }

      sanitizeNode(child)
    }
  }

  sanitizeNode(doc.body)
  return doc.body.innerHTML
}