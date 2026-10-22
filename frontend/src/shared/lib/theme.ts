import { create } from 'zustand'

type Theme = 'light' | 'dark' | 'system'

type ThemeStore = {
  theme: Theme
  setTheme: (theme: Theme) => void
  resolvedTheme: 'light' | 'dark'
}

export const useThemeStore = create<ThemeStore>((set) => ({
  theme: (localStorage.getItem('theme') as Theme) || 'system',
  resolvedTheme: 'light',
  setTheme: (theme) => {
    localStorage.setItem('theme', theme)
    set({ theme })
    
    // Apply theme to document
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')
    
    const resolved =
      theme === 'system'
        ? window.matchMedia('(prefers-color-scheme: dark)').matches
          ? 'dark'
          : 'light'
        : theme
    
    root.classList.add(resolved)
    set({ resolvedTheme: resolved })
  },
}))

// Initialize theme on load
if (typeof window !== 'undefined') {
  const store = useThemeStore.getState()
  store.setTheme(store.theme)
  
  // Watch for system theme changes
  window
    .matchMedia('(prefers-color-scheme: dark)')
    .addEventListener('change', (e) => {
      const current = useThemeStore.getState().theme
      if (current === 'system') {
        const root = window.document.documentElement
        root.classList.remove('light', 'dark')
        root.classList.add(e.matches ? 'dark' : 'light')
        useThemeStore.setState({ resolvedTheme: e.matches ? 'dark' : 'light' })
      }
    })
}
