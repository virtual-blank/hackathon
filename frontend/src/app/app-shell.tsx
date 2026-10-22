import { Outlet, useLocation } from 'react-router-dom'
import { DesktopSidebar } from './components/DesktopSidebar'
import { MobileBottomNav } from './components/MobileBottomNav'
import { CreateHabitSheet } from '@/features/habits/components/CreateHabitSheet'
import { ChatSocketProvider } from '@/features/social/hooks/ChatSocketProvider'
import { UnreadTitleSync } from './components/UnreadTitleSync'
import { ThemeSync } from '@/features/profile/hooks/useThemeSync'

const publicRoutes = ['/login', '/register', '/_design']

export function AppShell() {
  const location = useLocation()
  const isPublicRoute = publicRoutes.includes(location.pathname)

  if (isPublicRoute) {
    return (
      <div className="min-h-screen bg-background">
        <Outlet />
      </div>
    )
  }

  return (
    <ChatSocketProvider>
      <UnreadTitleSync />
      <ThemeSync />
      <div className="h-dvh bg-background flex overflow-hidden">
        <DesktopSidebar />
        
        <main className="flex-1 flex flex-col min-h-0 lg:p-3">
          <div className="flex-1 lg:bg-surface lg:rounded-[24px] lg:shadow-[0_1px_2px_rgba(20,20,30,0.04),0_8px_30px_rgba(20,20,30,0.06)] overflow-y-auto pb-20 lg:pb-0">
            <Outlet />
          </div>
        </main>

        <MobileBottomNav />
        <CreateHabitSheet />
      </div>
    </ChatSocketProvider>
  )
}

