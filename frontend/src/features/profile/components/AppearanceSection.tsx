import { useThemeStore } from '@/shared/lib/theme'
import { Monitor, Moon, Sun, Check } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import { SettingsSection } from './SettingsSection'

export function AppearanceSection() {
  const { theme, setTheme } = useThemeStore()

  const options = [
    { value: 'system' as const, icon: Monitor, label: 'Авто' },
    { value: 'light' as const, icon: Sun, label: 'Светлая' },
    { value: 'dark' as const, icon: Moon, label: 'Тёмная' },
  ]

  return (
    <SettingsSection title="Внешний вид">
      <div className="p-4">
        <div
          className="grid grid-cols-3 gap-3"
          role="radiogroup"
          aria-label="Выбор темы оформления"
        >
          {options.map(({ value, icon: Icon, label }) => {
            const isSelected = theme === value
            return (
              <label key={value} className="relative">
                <input
                  type="radio"
                  name="theme"
                  value={value}
                  checked={isSelected}
                  onChange={() => setTheme(value)}
                  className="sr-only"
                />
                <div
                  className={cn(
                    'flex flex-col items-center gap-3 p-3 rounded-xl cursor-pointer transition-all',
                    'hover:bg-muted/50 motion-reduce:transition-none',
                    isSelected &&
                      'ring-2 ring-foreground ring-offset-2 ring-offset-background'
                  )}
                  tabIndex={0}
                  role="radio"
                  aria-checked={isSelected}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      setTheme(value)
                    }
                  }}
                >
                  {/* Theme preview */}
                  <div className="relative w-full h-14 rounded-xl overflow-hidden border border-border">
                    {value === 'system' ? (
                      <div className="w-full h-full">
                        <div
                          className="absolute inset-0 bg-[var(--background)]"
                          style={{
                            clipPath: 'polygon(0 0, 100% 100%, 0 100%)',
                          }}
                        >
                          <div className="absolute bottom-1 left-1 w-8 h-8 bg-[var(--surface)] rounded" />
                        </div>
                        <div
                          className="absolute inset-0"
                          style={{
                            background: 'hsl(240 6% 10%)',
                            clipPath: 'polygon(100% 0, 100% 100%, 0 0)',
                          }}
                        >
                          <div className="absolute top-1 right-1 w-8 h-8 rounded"
                            style={{ background: 'hsl(240 4% 15%)' }}
                          />
                        </div>
                      </div>
                    ) : value === 'light' ? (
                      <div className="w-full h-full bg-[#F3F3F1] flex items-end justify-start p-1.5">
                        <div className="w-10 h-10 bg-white rounded shadow-sm" />
                      </div>
                    ) : (
                      <div
                        className="w-full h-full flex items-start justify-end p-1.5"
                        style={{ background: 'hsl(240 6% 10%)' }}
                      >
                        <div
                          className="w-10 h-10 rounded shadow-sm"
                          style={{ background: 'hsl(240 4% 15%)' }}
                        />
                      </div>
                    )}
                    {isSelected && (
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-6 h-6 rounded-full bg-foreground flex items-center justify-center">
                          <Check className="w-4 h-4 text-background" strokeWidth={2.5} />
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Icon className="w-4 h-4 text-muted-foreground" strokeWidth={1.75} />
                    <span className="text-sm font-medium">{label}</span>
                  </div>
                </div>
              </label>
            )
          })}
        </div>
      </div>
    </SettingsSection>
  )
}
