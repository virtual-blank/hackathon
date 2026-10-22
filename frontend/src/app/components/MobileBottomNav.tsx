import { NavLink, useLocation, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  CalendarCheck,
  TrendingUp,
  Users,
  MessageCircle,
  MoreHorizontal,
  Bell,
  Download,
  Settings,
  User,
  LogOut,
} from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/shared/ui/sheet'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Skeleton } from '@/shared/ui/skeleton'
import { ThemeSwitcher } from './ThemeSwitcher'
import { useGetMeApiV1UsersMeGet, useLogoutApiV1UsersLogoutPost } from '@/api/generated/👤-users/👤-users'
import { clearTokens } from '@/api/mutator'
import { useUnreadMessages } from '@/features/social/hooks/useUnreadMessages'
import defaultPfp from '@/assets/defaults/default-pfp.webp'

const mainNavItems = [
  { path: '/', icon: CalendarCheck, label: 'Привычки' },
  { path: '/feed', icon: TrendingUp, label: 'Лента' },
  { path: '/friends', icon: Users, label: 'Друзья' },
  { path: '/chat', icon: MessageCircle, label: 'Чат' },
]

const moreNavItems = [
  { path: '/notifications', icon: Bell, label: 'Уведомления' },
  { path: '/export', icon: Download, label: 'Экспорт' },
  { path: '/settings', icon: Settings, label: 'Настройки' },
]

export function MobileBottomNav() {
  const [moreOpen, setMoreOpen] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { mutate: logout } = useLogoutApiV1UsersLogoutPost()
  const { data: user, isLoading } = useGetMeApiV1UsersMeGet()
  const { hasUnreadMessages } = useUnreadMessages()

  const handleLogout = () => {
    logout(undefined, {
      onSettled: () => {
        clearTokens()
        queryClient.clear()
        navigate('/login')
      },
    })
  }

  const isMoreActive = moreNavItems.some((item) => item.path === location.pathname)

  return (
    <>
      <nav
        className="lg:hidden fixed bottom-0 left-0 right-0 bg-card border-t border-border z-50"
        style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
      >
        <div className="flex items-center justify-around h-16 px-2">
          {mainNavItems.map(({ path, icon: Icon, label }) => {
            const isChat = path === '/chat'
            
            return (
              <NavLink
                key={path}
                to={path}
                className={({ isActive }) =>
                  cn(
                    'flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg motion-safe:transition-colors min-w-[56px]',
                    isActive
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  )
                }
              >
                <span className="relative inline-flex shrink-0">
                  <Icon className="w-5 h-5" strokeWidth={1.75} />
                  {isChat && hasUnreadMessages && (
                    <span
                      className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-destructive ring-2 ring-card motion-safe:animate-in motion-safe:zoom-in-75"
                      aria-label="Есть непрочитанные сообщения"
                    />
                  )}
                </span>
                <span className="text-xs font-medium">{label}</span>
              </NavLink>
            )
          })}

          <button
            onClick={() => setMoreOpen(true)}
            className={cn(
              'flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg motion-safe:transition-colors min-w-[56px]',
              isMoreActive
                ? 'text-primary'
                : 'text-muted-foreground hover:text-foreground'
            )}
            aria-label="Ещё"
          >
            <MoreHorizontal className="w-5 h-5" strokeWidth={1.75} />
            <span className="text-xs font-medium">Ещё</span>
          </button>
        </div>
      </nav>

      <Sheet open={moreOpen} onOpenChange={setMoreOpen}>
        <SheetContent side="bottom" className="rounded-t-2xl">
          <SheetHeader className="mb-6">
            <div className="flex items-center gap-3">
              {isLoading ? (
                <>
                  <Skeleton className="w-12 h-12 rounded-full" />
                  <Skeleton className="h-5 w-32" />
                </>
              ) : (
                <>
                  <button
                    onClick={() => {
                      setMoreOpen(false)
                      navigate('/profile')
                    }}
                    className="shrink-0 hover:opacity-80 transition-opacity"
                    aria-label="Перейти в профиль"
                  >
                    <Avatar className="w-12 h-12">
                      <AvatarImage
                        src={user?.pfp_url || defaultPfp}
                        alt={user?.username}
                      />
                      <AvatarFallback>
                        <User className="w-6 h-6" />
                      </AvatarFallback>
                    </Avatar>
                  </button>
                  <div className="flex-1 text-left">
                    <SheetTitle className="text-lg">{user?.username}</SheetTitle>
                  </div>
                </>
              )}
            </div>
          </SheetHeader>

          <nav className="space-y-2 mb-6">
            {moreNavItems.map(({ path, icon: Icon, label }) => (
              <NavLink
                key={path}
                to={path}
                onClick={() => setMoreOpen(false)}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium motion-safe:transition-colors',
                    isActive
                      ? 'bg-surface-elevated text-foreground'
                      : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                  )
                }
              >
                <Icon className="w-5 h-5" strokeWidth={1.75} />
                <span>{label}</span>
              </NavLink>
            ))}
          </nav>

          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-4 py-3 rounded-lg text-base font-medium text-destructive hover:bg-muted transition-colors w-full text-left mb-4"
          >
            <LogOut className="w-5 h-5" strokeWidth={1.75} />
            <span>Выйти из аккаунта</span>
          </button>

          <div className="border-t border-border pt-4">
            <ThemeSwitcher />
          </div>
        </SheetContent>
      </Sheet>
    </>
  )
}

