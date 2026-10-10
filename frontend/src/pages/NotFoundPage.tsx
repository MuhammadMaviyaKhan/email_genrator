import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'
import Button from '@/components/ui/Button'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="animated-bg absolute inset-0 pointer-events-none" />
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative z-10 text-center"
      >
        <motion.h1
          initial={{ y: -20 }}
          animate={{ y: 0 }}
          className="text-9xl font-bold gradient-text mb-4"
        >
          404
        </motion.h1>
        <h2 className="text-2xl font-semibold text-dark-100 mb-2">Page Not Found</h2>
        <p className="text-dark-400 mb-8 max-w-md">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link to="/">
            <Button variant="gradient" leftIcon={<Home className="w-4 h-4" />}>
              Go Home
            </Button>
          </Link>
          <Link to="/generate">
            <Button variant="secondary" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Generate Email
            </Button>
          </Link>
        </div>
      </motion.div>
    </div>
  )
}