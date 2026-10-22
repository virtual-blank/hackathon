import { useThemeStore } from '@/shared/lib/theme'
import { Monitor, Moon, Sun } from 'lucide-react'
import { cn } from '@/shared/lib/utils'

export function ThemeSwitcher() {
  const { theme, setTheme } = useThemeStore()

  const options = [
    { value: 'system' as const, icon: Monitor, label: 'Авто' },
    { value: 'light' as const, icon: Sun, label: 'Светлая' },
    { value: 'dark' as const, icon: Moon, label: 'Тёмная' },
  ]

  return (
    <div className="flex items-center gap-1 p-1 bg-surface-muted rounded-lg">
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={cn(
            'flex items-center justify-center flex-1 py-2 rounded-md text-sm font-medium transition-colors',
            theme === value
              ? 'bg-surface-elevated text-foreground shadow-[0_1px_2px_rgba(20,20,30,0.04)]'
              : 'text-muted-foreground hover:text-foreground'
          )}
          aria-label={label}
        >
          <Icon className="w-5 h-5" strokeWidth={1.75} />
        </button>
      ))}
    </div>
  )
}
