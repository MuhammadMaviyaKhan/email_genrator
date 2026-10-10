import { motion } from 'framer-motion'
import { ArrowRight, Info } from 'lucide-react'
import { Link } from 'react-router-dom'
import GenerateEmail from '@/components/email/GenerateEmail'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'

export default function GeneratePage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8 text-center"
      >
        <h1 className="text-3xl font-bold text-dark-100 mb-2">Generate Temporary Email</h1>
        <p className="text-dark-400">
          Create a secure, disposable email address in seconds
        </p>
      </motion.div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <GenerateEmail />
        </div>

        <div className="space-y-4">
          <Card glass className="p-6">
            <div className="flex items-center gap-2 mb-4">
              <Info className="w-5 h-5 text-primary-400" />
              <h3 className="font-semibold text-dark-100">How it works</h3>
            </div>
            <ol className="space-y-3 text-sm text-dark-400">
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-500/20 text-primary-300 flex items-center justify-center text-xs font-bold">
                  1
                </span>
                Generate a random or custom email address
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-500/20 text-primary-300 flex items-center justify-center text-xs font-bold">
                  2
                </span>
                Use it to sign up for services anonymously
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-500/20 text-primary-300 flex items-center justify-center text-xs font-bold">
                  3
                </span>
                Receive emails in real-time on this dashboard
              </li>
              <li className="flex gap-3">
                <span className="flex-shrink-0 w-6 h-6 rounded-full bg-primary-500/20 text-primary-300 flex items-center justify-center text-xs font-bold">
                  4
                </span>
                Auto-expires and deletes after set time
              </li>
            </ol>
          </Card>

          <Card glass className="p-6">
            <h3 className="font-semibold text-dark-100 mb-3">Need to check your inbox?</h3>
            <Link to="/inbox">
              <Button variant="gradient" fullWidth rightIcon={<ArrowRight className="w-4 h-4" />}>
                Go to Inbox
              </Button>
            </Link>
          </Card>
        </div>
      </div>
    </div>
  )
}