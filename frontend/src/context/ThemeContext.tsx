import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { ThemeOption, THEME_OPTIONS, STORAGE_KEYS } from '@/utils/constants'

interface ThemeContextType {
  theme: ThemeOption
  setTheme: (theme: ThemeOption) => void
  resolvedTheme: 'light' | 'dark'
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeOption>(() => {
    const stored = localStorage.getItem(STORAGE_KEYS.THEME) as ThemeOption | null
    return stored && THEME_OPTIONS.includes(stored) ? stored : 'dark'
  })

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>('dark')

  useEffect(() => {
    const root = document.documentElement
    
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const updateTheme = () => {
        setResolvedTheme(mediaQuery.matches ? 'dark' : 'light')
        root.classList.toggle('dark', mediaQuery.matches)
      }
      updateTheme()
      mediaQuery.addEventListener('change', updateTheme)
      return () => mediaQuery.removeEventListener('change', updateTheme)
    } else {
      setResolvedTheme(theme)
      root.classList.toggle('dark', theme === 'dark')
    }
  }, [theme])

  const setTheme = (newTheme: ThemeOption) => {
    setThemeState(newTheme)
    localStorage.setItem(STORAGE_KEYS.THEME, newTheme)
  }

  const toggleTheme = () => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return context
}