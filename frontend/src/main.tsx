import { StrictMode, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { Providers } from './app/providers'
import { ThemeProvider } from './app/theme-provider'
import { Router } from './app/router'
import { loadTokensFromStorage } from './api/mutator'
import './styles/index.css'

// Load tokens from localStorage on app start
loadTokensFromStorage()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Providers>
      <ThemeProvider>
        <Suspense
          fallback={
            <div className="flex min-h-screen items-center justify-center">
              <div className="animate-pulse text-muted-foreground">
                Загрузка...
              </div>
            </div>
          }
        >
          <Router />
        </Suspense>
      </ThemeProvider>
    </Providers>
  </StrictMode>
)

