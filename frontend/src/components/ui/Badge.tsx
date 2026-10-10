import { ReactNode } from 'react'
import { cn } from '@/utils/cn'

interface BadgeProps {
  children: ReactNode
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral'
  className?: string
  dot?: boolean
}

const variantClasses = {
  primary: 'badge-primary',
  success: 'badge-success',
  warning: 'badge-warning',
  danger: 'badge-danger',
  neutral: 'badge bg-dark-800 text-dark-300',
}

const dotColors = {
  primary: 'bg-primary-400',
  success: 'bg-green-400',
  warning: 'bg-yellow-400',
  danger: 'bg-red-400',
  neutral: 'bg-dark-400',
}

export const Badge = ({ children, variant = 'neutral', className, dot }: BadgeProps) => (
  <span className={cn(variantClasses[variant], className)}>
    {dot && <span className={cn('w-1.5 h-1.5 rounded-full', dotColors[variant])} />}
    {children}
  </span>
)

export default Badge