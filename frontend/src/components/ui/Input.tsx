import { ReactNode, InputHTMLAttributes, forwardRef, useState } from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { Eye, EyeOff } from 'lucide-react'
import { cn } from '@/utils/cn'
import { useTheme } from '@/context/ThemeContext'

interface InputProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'ref'> {
  label?: string
  error?: string
  icon?: ReactNode
  rightIcon?: ReactNode
  fullWidth?: boolean
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, rightIcon, fullWidth, className, type, ...props }, ref) => {
    const { resolvedTheme } = useTheme()
    const [showPassword, setShowPassword] = useState(false)
    const isPassword = type === 'password'
    const inputType = isPassword ? (showPassword ? 'text' : 'password') : type

    return (
      <div className={cn('flex flex-col gap-1.5', fullWidth && 'w-full')}>
        {label && (
          <label className="text-sm font-medium text-dark-300 dark:text-dark-300 light:text-gray-600">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-dark-400">
              {icon}
            </span>
          )}
          <motion.input
            ref={ref}
            type={inputType}
            className={cn(
              resolvedTheme === 'dark' ? 'input' : 'input-light',
              icon && 'pl-10',
              (isPassword || rightIcon) && 'pr-10',
              error && 'border-red-500 focus:ring-red-500/20',
              className
            )}
            {...(props as HTMLMotionProps<'input'>)}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400 hover:text-dark-200 transition-colors"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          )}
          {rightIcon && !isPassword && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400">
              {rightIcon}
            </span>
          )}
        </div>
        {error && <span className="text-xs text-red-400">{error}</span>}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input