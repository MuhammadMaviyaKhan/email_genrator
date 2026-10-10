import { ReactNode } from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { cn } from '@/utils/cn'
import { useTheme } from '@/context/ThemeContext'

interface CardProps extends Omit<HTMLMotionProps<'div'>, 'ref'> {
  children: ReactNode
  hover?: boolean
  glass?: boolean
  glow?: boolean
}

const Card = ({ children, hover, glass, glow, className, ...props }: CardProps) => {
  const { resolvedTheme } = useTheme()

  return (
    <motion.div
      whileHover={hover ? { y: -4, scale: 1.01 } : undefined}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      className={cn(
        resolvedTheme === 'dark'
          ? glass
            ? 'card'
            : 'bg-dark-900 border border-dark-800 rounded-2xl'
          : glass
          ? 'card-light'
          : 'bg-white border border-gray-200 rounded-2xl shadow-sm',
        glow && 'shadow-glow',
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  )
}

const CardHeader = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('px-6 py-4 border-b border-dark-800/50', className)}>{children}</div>
)

const CardContent = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('px-6 py-4', className)}>{children}</div>
)

const CardFooter = ({ children, className }: { children: ReactNode; className?: string }) => (
  <div className={cn('px-6 py-4 border-t border-dark-800/50', className)}>{children}</div>
)

Card.Header = CardHeader
Card.Content = CardContent
Card.Footer = CardFooter

export default Card