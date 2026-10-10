import { ReactNode } from 'react'
import { motion } from 'framer-motion'

interface EmptyStateProps {
  icon: ReactNode
  title: string
  description?: string
  action?: ReactNode
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-16 px-4 text-center"
    >
      <motion.div
        initial={{ scale: 0, rotate: -10 }}
        animate={{ scale: 1, rotate: 0 }}
        transition={{ type: 'spring', stiffness: 200, damping: 15 }}
        className="p-4 rounded-2xl bg-dark-800/50 text-dark-500 mb-4"
      >
        {icon}
      </motion.div>
      <h3 className="text-lg font-semibold text-dark-200 mb-2">{title}</h3>
      {description && (
        <p className="text-sm text-dark-400 max-w-sm mb-6">{description}</p>
      )}
      {action}
    </motion.div>
  )
}