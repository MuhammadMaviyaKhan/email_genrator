import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Mail, Shield, Zap, Globe, Clock, Lock, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react'
import Button from '@/components/ui/Button'
import Card from '@/components/ui/Card'

const features = [
  {
    icon: <Zap className="w-6 h-6" />,
    title: 'Instant Generation',
    description: 'Create a temporary email address with just one click. No registration required.',
  },
  {
    icon: <Shield className="w-6 h-6" />,
    title: 'Privacy First',
    description: 'Protect your real inbox from spam, trackers, and unwanted marketing emails.',
  },
  {
    icon: <Globe className="w-6 h-6" />,
    title: 'Multiple Domains',
    description: 'Choose from various premium domains for your temporary email address.',
  },
  {
    icon: <Clock className="w-6 h-6" />,
    title: 'Auto Expiry',
    description: 'Emails automatically expire and get deleted. Set custom expiry times.',
  },
  {
    icon: <Lock className="w-6 h-6" />,
    title: 'OTP Detection',
    description: 'Automatically detects and extracts OTP codes and verification links.',
  },
  {
    icon: <Sparkles className="w-6 h-6" />,
    title: 'Real-time Inbox',
    description: 'WebSocket-powered live updates. Emails appear instantly in your inbox.',
  },
]

const stats = [
  { label: 'Emails Generated', value: '2.5M+' },
  { label: 'Active Domains', value: '25+' },
  { label: 'Uptime', value: '99.9%' },
  { label: 'Avg. Delivery', value: '<2s' },
]

export default function HomePage() {
  return (
    <div className="relative">
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', stiffness: 200, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/30 text-primary-300 text-sm mb-6"
            >
              <Sparkles className="w-4 h-4" />
              Secure Temporary Email Service
            </motion.div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-dark-100 mb-6 leading-tight">
              Protect Your Inbox with{' '}
              <span className="gradient-text">TempMail Pro</span>
            </h1>

            <p className="text-lg text-dark-400 max-w-2xl mx-auto mb-8">
              Generate disposable email addresses instantly. Keep your real inbox clean and secure
              from spam, bots, and unwanted mail.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link to="/generate">
                <Button variant="gradient" size="lg" leftIcon={<Mail className="w-5 h-5" />}>
                  Get Started Free
                  <ArrowRight className="w-4 h-4 ml-1" />
                </Button>
              </Link>
              <Link to="/inbox">
                <Button variant="secondary" size="lg">
                  Open Inbox
                </Button>
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-16"
          >
            {stats.map((stat, idx) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.4 + idx * 0.1 }}
              >
                <Card glass className="p-6 text-center">
                  <p className="text-3xl font-bold gradient-text mb-1">{stat.value}</p>
                  <p className="text-sm text-dark-400">{stat.label}</p>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold text-dark-100 mb-4">
              Everything You Need
            </h2>
            <p className="text-dark-400 max-w-2xl mx-auto">
              Powerful features designed for privacy-conscious users who want control over their inbox.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
              >
                <Card hover glass className="p-6 h-full">
                  <div className="p-3 rounded-xl bg-primary-500/15 w-fit mb-4 text-primary-400">
                    {feature.icon}
                  </div>
                  <h3 className="text-lg font-semibold text-dark-100 mb-2">{feature.title}</h3>
                  <p className="text-dark-400 text-sm">{feature.description}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative overflow-hidden rounded-3xl border border-primary-500/30 bg-gradient-to-br from-primary-500/10 to-cyan-500/5 p-8 sm:p-12 text-center"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-transparent pointer-events-none" />
            <div className="relative">
              <h2 className="text-3xl font-bold text-dark-100 mb-4">
                Start Protecting Your Privacy Today
              </h2>
              <p className="text-dark-400 mb-8 max-w-xl mx-auto">
                Join thousands of users who trust TempMail Pro for their temporary email needs.
              </p>
              <Link to="/generate">
                <Button variant="gradient" size="lg" leftIcon={<Mail className="w-5 h-5" />}>
                  Generate Your Email
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="py-16 border-t border-dark-800/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              { icon: <CheckCircle2 className="w-5 h-5 text-green-400" />, text: 'No registration required' },
              { icon: <CheckCircle2 className="w-5 h-5 text-green-400" />, text: 'End-to-end encryption' },
              { icon: <CheckCircle2 className="w-5 h-5 text-green-400" />, text: 'Open source & transparent' },
              { icon: <CheckCircle2 className="w-5 h-5 text-green-400" />, text: 'Auto-delete after expiry' },
              { icon: <CheckCircle2 className="w-5 h-5 text-green-400" />, text: 'Real-time notifications' },
              { icon: <CheckCircle2 className="w-5 h-5 text-green-400" />, text: 'Mobile responsive design' },
            ].map((item, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -10 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.05 }}
                className="flex items-center gap-3"
              >
                {item.icon}
                <span className="text-dark-300 text-sm">{item.text}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}