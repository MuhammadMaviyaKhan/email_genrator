import { Link } from 'react-router-dom'
import { Mail, Github, Twitter, Shield } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t border-dark-800/50 bg-dark-950/50 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1.5 rounded-lg bg-gradient-to-br from-primary-500 to-cyan-500">
                <Mail className="w-4 h-4 text-white" />
              </div>
              <span className="text-lg font-bold gradient-text">TempMail Pro</span>
            </div>
            <p className="text-sm text-dark-400 max-w-sm">
              Secure, private, and temporary email addresses. Protect your real inbox from spam,
              bots, and unwanted mail.
            </p>
            <div className="flex items-center gap-3 mt-4">
              <a href="#" className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 transition-colors">
                <Github className="w-4 h-4 text-dark-300" />
              </a>
              <a href="#" className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 transition-colors">
                <Twitter className="w-4 h-4 text-dark-300" />
              </a>
              <a href="#" className="p-2 rounded-lg bg-dark-800 hover:bg-dark-700 transition-colors">
                <Shield className="w-4 h-4 text-dark-300" />
              </a>
            </div>
          </div>

          <div>
            <h4 className="font-semibold text-dark-200 mb-3">Product</h4>
            <ul className="flex flex-col gap-2 text-sm text-dark-400">
              <li><Link to="/" className="hover:text-primary-400 transition-colors">Home</Link></li>
              <li><Link to="/generate" className="hover:text-primary-400 transition-colors">Generate Email</Link></li>
              <li><Link to="/inbox" className="hover:text-primary-400 transition-colors">Inbox</Link></li>
              <li><a href="#" className="hover:text-primary-400 transition-colors">API Docs</a></li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-dark-200 mb-3">Legal</h4>
            <ul className="flex flex-col gap-2 text-sm text-dark-400">
              <li><a href="#" className="hover:text-primary-400 transition-colors">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-primary-400 transition-colors">Terms of Service</a></li>
              <li><a href="#" className="hover:text-primary-400 transition-colors">Cookie Policy</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-dark-800/50 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-dark-500">
            © {new Date().getFullYear()} TempMail Pro. All rights reserved.
          </p>
          <p className="text-xs text-dark-500 flex items-center gap-1">
            <Shield className="w-3 h-3" />
            Secured with end-to-end encryption
          </p>
        </div>
      </div>
    </footer>
  )
}