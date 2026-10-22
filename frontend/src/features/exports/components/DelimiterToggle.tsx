import { ExportDelimiter } from '@/api/generated/model'
import { AlertCircle } from 'lucide-react'
import { cn } from '@/shared/lib/utils'

type Props = {
  value: ExportDelimiter
  onChange: (d: ExportDelimiter) => void
}

export function DelimiterToggle({ value, onChange }: Props) {
  const options: Array<{ value: ExportDelimiter; label: React.ReactNode }> = [
    {
      value: ExportDelimiter[';'],
      label: (
        <>
          Точка с запятой<span className="ml-1.5 font-mono">;</span>
        </>
      ),
    },
    {
      value: ExportDelimiter[','],
      label: (
        <>
          Запятая<span className="ml-1.5 font-mono">,</span>
        </>
      ),
    },
  ]

  const hints: Record<ExportDelimiter, string> = {
    [ExportDelimiter[';']]: 'Для русскоязычного Excel',
    [ExportDelimiter[',']]: 'Для Google Таблиц и международного Excel',
  }

  return (
    <div className="space-y-2">
      {/* Row with label and pill control */}
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
        <label className="shrink-0 whitespace-nowrap text-sm font-medium">
          Разделитель колонок
        </label>
        <div role="radiogroup" className="inline-flex rounded-full bg-muted p-1 gap-1">
          {options.map((opt) => (
            <label
              key={opt.value}
              className={cn(
                'relative flex items-center justify-center px-4 h-11 rounded-full cursor-pointer transition-all text-sm font-medium',
                value === opt.value
                  ? 'bg-surface-elevated shadow-sm text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              <input
                type="radio"
                name="delimiter"
                value={opt.value}
                checked={value === opt.value}
                onChange={() => onChange(opt.value)}
                className="sr-only"
              />
              {opt.label}
            </label>
          ))}
        </div>
      </div>

      {/* Dynamic hint with animation */}
      <div className="min-h-5" aria-live="polite">
        <p
          key={value}
          className={cn(
            'flex items-center gap-1.5 text-[13px] text-muted-foreground',
            'motion-safe:animate-in motion-safe:fade-in-0 motion-safe:zoom-in-95 motion-safe:slide-in-from-bottom-1 motion-safe:duration-200 motion-safe:ease-out'
          )}
        >
          <AlertCircle
            className="w-3.5 h-3.5 shrink-0 text-muted-foreground opacity-70"
            strokeWidth={1.75}
            aria-hidden
          />
          {hints[value]}
        </p>
      </div>
    </div>
  )
}
