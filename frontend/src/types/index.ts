export interface EmailAddress {
  id: string
  email: string
  local_part: string
  domain: string
  status: 'active' | 'expired' | 'blocked' | 'deleted'
  expires_at: string
  created_at: string
  updated_at: string
  last_accessed_at: string | null
  emails_count: number
  max_emails: number
  is_custom: boolean
  token?: string
}

export interface EmailAttachment {
  filename: string
  content_type: string
  size: number
  content_id?: string | null
  is_inline: boolean
  download_url?: string | null
}

export interface Email {
  id: string
  email_address_id: string
  message_id: string
  subject: string | null
  from_address: string
  from_name: string | null
  to_addresses: string[] | null
  cc_addresses: string[] | null
  bcc_addresses: string[] | null
  reply_to: string | null
  text_body: string | null
  html_body: string | null
  raw_source: string | null
  headers: Record<string, any> | null
  attachments: EmailAttachment[] | null
  status: 'received' | 'read' | 'deleted' | 'expired' | 'failed'
  size_bytes: number
  received_at: string
  read_at: string | null
  deleted_at: string | null
  spam_score: number | null
  is_spam: boolean
}

export interface EmailDetail extends Email {
  otp_codes: OTPCode[]
  verification_links: VerificationLink[]
}

export interface OTPCode {
  code: string
  length: number
  source: string
  context?: string | null
}

export interface VerificationLink {
  url: string
  text: string
  type: string
}

export interface EmailList {
  emails: Email[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface EmailAddressList {
  items: EmailAddress[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface GenerateEmailResponse {
  email: EmailAddress
  token: string
  password: string | null
  expires_at: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  email: EmailAddress
  session_token: string
}

export interface StatsResponse {
  total_emails: number
  emails_today: number
  emails_this_week: number
  emails_this_month: number
  max_emails: number
  remaining_emails: number
  expires_at: string | null
  is_expired: boolean
  email?: EmailAddress
}

export interface HealthResponse {
  status: string
  version: string
  environment: string
  database: string
  redis: string
  smtp: string
  uptime_seconds: number
  websocket_connections: number
  active_addresses: number
}

export interface WebSocketMessage {
  type: string
  data?: any
  timestamp: string
}

export interface ApiError {
  detail: string
  code?: string
  details?: Record<string, any>
}