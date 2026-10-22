import { cn } from '@/shared/lib/utils'

type SettingsSectionProps = {
  title: string
  description?: string
  children: React.ReactNode
  className?: string
}

export function SettingsSection({
  title,
  description,
  children,
  className,
}: SettingsSectionProps) {
  return (
    <section className={cn('space-y-4', className)}>
      <div>
        <h2 className="font-serif text-[20px] font-semibold leading-tight">
          {title}
        </h2>
        {description && (
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        )}
      </div>
      <div className="bg-surface-muted/50 rounded-2xl overflow-hidden">
        {children}
      </div>
    </section>
  )
}

type SettingsRowProps = {
  label: string
  description?: string
  children: React.ReactNode
  isLast?: boolean
}

export function SettingsRow({
  label,
  description,
  children,
  isLast,
}: SettingsRowProps) {
  return (
    <div
      className={cn(
        'min-h-14 px-4 py-3 flex items-center justify-between gap-4',
        !isLast && 'border-b border-border/60'
      )}
    >
      <div className="flex-1 min-w-0">
        <div className="text-[15px] font-medium">{label}</div>
        {description && (
          <div className="text-sm text-muted-foreground mt-0.5">
            {description}
          </div>
        )}
      </div>
      <div className="flex items-center gap-2 shrink-0">{children}</div>
    </div>
  )
}
