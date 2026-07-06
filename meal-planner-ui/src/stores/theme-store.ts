import { create } from 'zustand'

interface ThemeState {
  isDark: boolean
  toggle: () => void
}

function getInitialTheme(): boolean {
  const stored = localStorage.getItem('theme')
  if (stored === 'dark') return true
  if (stored === 'light') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

const initial = getInitialTheme()
if (initial) {
  document.documentElement.classList.add('dark')
}

export const useThemeStore = create<ThemeState>((set) => ({
  isDark: initial,
  toggle: () =>
    set((state) => {
      const next = !state.isDark
      document.documentElement.classList.toggle('dark', next)
      localStorage.setItem('theme', next ? 'dark' : 'light')
      return { isDark: next }
    }),
}))
