import { useState } from 'react'
import { cn } from '@/shared/lib/utils'
import { shiftDays, startOfYear } from '../../lib/dates'
import { CustomDateRange } from './CustomDateRange'

type Props = {
  value: string
  onChange: (type: string) => void
  today: string
  customFrom: string
  customTo: string
  onCustomFromChange: (v: string) => void
  onCustomToChange: (v: string) => void
}

const PRESETS = [
  { id: 'all', label: 'Всё время' },
  { id: '30', label: '30 дней' },
  { id: '90', label: '90 дней' },
  { id: 'year', label: 'Этот год' },
  { id: 'custom', label: 'Свой период' },
]

export function PeriodPicker({
  value,
  onChange,
  today,
  customFrom,
  customTo,
  onCustomFromChange,
  onCustomToChange,
}: Props) {
  const [internalValue, setInternalValue] = useState(value)

  const handleSelect = (id: string) => {
    setInternalValue(id)
    if (id === 'all') {
      onChange('all')
    } else if (id === '30') {
      onCustomFromChange(shiftDays(today, -29))
      onCustomToChange(today)
      onChange('custom')
    } else if (id === '90') {
      onCustomFromChange(shiftDays(today, -89))
      onCustomToChange(today)
      onChange('custom')
    } else if (id === 'year') {
      onCustomFromChange(startOfYear(today))
      onCustomToChange(today)
      onChange('custom')
    } else if (id === 'custom') {
      if (!customFrom && !customTo) {
        onCustomFromChange(shiftDays(today, -29))
        onCustomToChange(today)
      }
      onChange('custom')
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {PRESETS.map((preset) => (
          <button
            key={preset.id}
            type="button"
            onClick={() => handleSelect(preset.id)}
            className={cn(
              'px-3 h-9 rounded-full text-sm font-medium transition-all',
              internalValue === preset.id
                ? 'bg-surface-elevated shadow-sm text-foreground'
                : 'bg-muted text-muted-foreground hover:text-foreground'
            )}
          >
            {preset.label}
          </button>
        ))}
      </div>

      {internalValue === 'custom' && (
        <CustomDateRange
          from={customFrom}
          to={customTo}
          onFromChange={onCustomFromChange}
          onToChange={onCustomToChange}
          maxDate={today}
        />
      )}
    </div>
  )
}
