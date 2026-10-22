import { NavLink, useNavigate } from 'react-router-dom'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Skeleton } from '@/shared/ui/skeleton'
import { ThemeSwitcher } from './ThemeSwitcher'
import { Button } from '@/shared/ui/button'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/shared/ui/tooltip'
import { cn } from '@/shared/lib/utils'
import { useAppShellStore } from '@/shared/lib/app-shell-store'
import { useUnreadMessages } from '@/features/social/hooks/useUnreadMessages'
import {
  CalendarCheck,
  TrendingUp,
  Users,
  Bell,
  MessageCircle,
  Download,
  Settings,
  Menu,
  Plus,
} from 'lucide-react'
import defaultPfp from '@/assets/defaults/default-pfp.webp'

const navItems = [
  { path: '/', icon: CalendarCheck, label: 'Привычки' },
  { path: '/feed', icon: TrendingUp, label: 'Лента' },
  { path: '/friends', icon: Users, label: 'Друзья' },
  { path: '/notifications', icon: Bell, label: 'Уведомления' },
  { path: '/chat', icon: MessageCircle, label: 'Чат' },
  { path: '/export', icon: Download, label: 'Экспорт' },
  { path: '/settings', icon: Settings, label: 'Настройки' },
]

export function DesktopSidebar() {
  const navigate = useNavigate()
  const { data: user, isLoading } = useGetMeApiV1UsersMeGet()
  const { sidebarCollapsed, setSidebarCollapsed, setCreateHabitSheetOpen } =
    useAppShellStore()
  const { hasUnreadMessages } = useUnreadMessages()

  return (
    <aside
      className={cn(
        'hidden lg:flex flex-col shrink-0 overflow-hidden',
        'motion-safe:transition-[width] motion-safe:duration-200',
        sidebarCollapsed ? 'w-[72px] sidebar-collapsed' : 'w-64'
      )}
    >
      {/* Header with burger */}
      <div className="flex items-center shrink-0 p-4 relative h-[72px]">
        {!sidebarCollapsed && (
          <div className="flex items-center gap-3 min-w-0 flex-1 mr-2">
            {isLoading ? (
              <>
                <Skeleton className="w-10 h-10 rounded-full" />
                <Skeleton className="h-4 w-24" />
              </>
            ) : (
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-3 min-w-0 flex-1 hover:bg-muted rounded-lg p-2 transition-colors"
              >
                <Avatar className="w-10 h-10">
                  <AvatarImage
                    src={user?.pfp_url || defaultPfp}
                    alt={user?.username}
                  />
                  <AvatarFallback>
                    {user?.username?.[0]?.toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <span className="font-semibold text-sm text-foreground truncate">
                  {user?.username}
                </span>
              </button>
            )}
          </div>
        )}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className={cn(
            'p-2 hover:bg-muted rounded-md motion-safe:transition-colors shrink-0',
            'w-11 h-11 flex items-center justify-center',
            sidebarCollapsed && 'absolute left-1/2 -translate-x-1/2'
          )}
          aria-label={sidebarCollapsed ? 'Развернуть сайдбар' : 'Свернуть сайдбар'}
        >
          <Menu className="w-5 h-5" strokeWidth={1.75} />
        </button>
      </div>

      {/* Navigation - scrollable */}
      <nav className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden p-3 space-y-1 sidebar-nav-list">
        <TooltipProvider delayDuration={0}>
          {navItems.map(({ path, icon: Icon, label }) => {
            const isChat = path === '/chat'
            return (
              <Tooltip key={path} open={sidebarCollapsed ? undefined : false}>
                <TooltipTrigger asChild>
                  <NavLink
                    to={path}
                    aria-label={isChat && hasUnreadMessages ? `${label}, есть непрочитанные сообщения` : label}
                    onPointerMove={(e) => {
                      if (sidebarCollapsed) {
                        const rect = e.currentTarget.getBoundingClientRect()
                        const x = ((e.clientX - rect.left) / rect.width) * 100
                        const y = ((e.clientY - rect.top) / rect.height) * 100
                        e.currentTarget.style.setProperty('--mouse-x', `${x}%`)
                        e.currentTarget.style.setProperty('--mouse-y', `${y}%`)
                      }
                    }}
                    className="relative flex w-full h-11 items-center gap-3 rounded-full pl-[14px] pr-3 text-[15px] font-medium sidebar-nav-item focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                  >
                    <span className="relative inline-flex shrink-0">
                      <Icon className="w-5 h-5" strokeWidth={1.75} />
                      {isChat && hasUnreadMessages && (
                        <span
                          className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-destructive ring-2 ring-background motion-safe:animate-in motion-safe:zoom-in-75"
                          aria-label="Есть непрочитанные сообщения"
                        />
                      )}
                    </span>
                    <span
                      aria-hidden={sidebarCollapsed}
                      className={cn(
                        'whitespace-nowrap motion-safe:transition-opacity motion-safe:duration-150',
                        sidebarCollapsed ? 'opacity-0' : 'opacity-100'
                      )}
                    >
                      {label}
                    </span>
                  </NavLink>
                </TooltipTrigger>
                <TooltipContent side="right" sideOffset={12} className="sidebar-tooltip-pill border-border/80">
                  <p>{label}</p>
                </TooltipContent>
              </Tooltip>
            )
          })}
        </TooltipProvider>
      </nav>

      {/* Bottom section - always visible */}
      <div className="shrink-0 py-3 space-y-3">
        <div className="px-3">
          <TooltipProvider delayDuration={0}>
            <Tooltip open={sidebarCollapsed ? undefined : false}>
              <TooltipTrigger asChild>
                <Button
                  onClick={() => setCreateHabitSheetOpen(true)}
                  variant="default"
                  aria-label="Создать привычку"
                  className="flex w-full h-11 items-center justify-start gap-3 overflow-hidden rounded-xl px-0 pl-[14px] pr-3 shadow-[0_4px_14px_rgba(20,20,30,0.16)] dark:shadow-none"
                >
                  <Plus className="w-5 h-5 shrink-0" strokeWidth={1.75} />
                  <span
                    aria-hidden={sidebarCollapsed}
                    className={cn(
                      'whitespace-nowrap motion-safe:transition-opacity motion-safe:duration-150',
                      sidebarCollapsed ? 'opacity-0' : 'opacity-100'
                    )}
                  >
                    Создать привычку
                  </span>
                </Button>
              </TooltipTrigger>
              <TooltipContent side="right" sideOffset={12} className="sidebar-tooltip-pill border-border/80">
                <p>Создать привычку</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
        {!sidebarCollapsed && (
          <div className="px-3">
            <div className="w-[232px]">
              <ThemeSwitcher />
            </div>
          </div>
        )}
      </div>
    </aside>
  )
}

