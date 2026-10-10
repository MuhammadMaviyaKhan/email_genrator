const resolveWsOrigin = (): string => {
  if (typeof window === 'undefined') return ''
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${protocol}://${window.location.host}`
}

export const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string) || '/api/v1'

export const WEBSOCKET_URL =
  (import.meta.env.VITE_WS_URL as string) || `${resolveWsOrigin()}/api/v1`

export const STORAGE_KEYS = {
  TOKEN: 'tempmail_token',
  EMAIL_ID: 'tempmail_email_id',
  THEME: 'tempmail_theme',
  EMAIL_DATA: 'tempmail_email_data',
} as const

export const ROUTES = {
  HOME: '/',
  GENERATE: '/generate',
  INBOX: '/inbox',
  EMAIL_VIEW: '/email/:id',
  ADMIN_LOGIN: '/admin/login',
  ADMIN_DASHBOARD: '/admin',
  ADMIN_EMAILS: '/admin/emails',
  ADMIN_LOGS: '/admin/logs',
} as const

export const EMAIL_TTL_PRESETS = [
  { label: '10 minutes', minutes: 10 },
  { label: '1 hour', minutes: 60 },
  { label: '24 hours', minutes: 1440 },
  { label: '7 days', minutes: 10080 },
  { label: '30 days', minutes: 43200 },
]

export const ITEMS_PER_PAGE = 20

export const REFRESH_INTERVAL = 2000

export const ADMIN_TOKEN_KEY = 'tempmail_admin_token'

export const THEME_OPTIONS = ['light', 'dark', 'system'] as const
export type ThemeOption = (typeof THEME_OPTIONS)[number]