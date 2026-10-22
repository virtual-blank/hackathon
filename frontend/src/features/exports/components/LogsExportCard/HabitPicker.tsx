import { useState } from 'react'
import { ChevronsUpDown, Check } from 'lucide-react'
import { Button } from '@/shared/ui/button'
import { Popover, PopoverTrigger, PopoverContent } from '@/shared/ui/popover'
import { useGetHabitsApiV1HabitsGet } from '@/api/generated/🏃-habits/🏃-habits'
import type { HabitOutputSchema } from '@/api/generated/model'
import { cn } from '@/shared/lib/utils'

type Props = {
  habitId: string | undefined
  habitTitle: string
  onSelect: (id: string | undefined, title: string) => void
  loading: boolean
}

export function HabitPicker({ habitId, habitTitle, onSelect, loading }: Props) {
  const [open, setOpen] = useState(false)
  const { data: habits } = useGetHabitsApiV1HabitsGet({ limit: 100, offset: 0 })

  const handleSelect = (id: string | undefined, title: string) => {
    onSelect(id, title)
    setOpen(false)
  }

  const displayLabel = habitId ? habitTitle : 'Все привычки'

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2" disabled={loading}>
          {displayLabel}
          <ChevronsUpDown className="w-4 h-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64 p-2" align="end">
        <div role="listbox" className="max-h-[280px] overflow-y-auto space-y-1">
          <button
            type="button"
            role="option"
            aria-selected={!habitId}
            onClick={() => handleSelect(undefined, '')}
            className={cn(
              'w-full flex items-center gap-2 px-3 h-9 rounded-md text-sm hover:bg-muted transition-colors',
              !habitId && 'bg-muted'
            )}
          >
            {!habitId && <Check className="w-4 h-4" />}
            <span className="flex-1 text-left">Все привычки</span>
          </button>

          {habits && habits.length > 0 ? (
            habits.map((h: HabitOutputSchema) => (
              <button
                key={h.id}
                type="button"
                role="option"
                aria-selected={habitId === h.id}
                onClick={() => handleSelect(h.id, h.title)}
                className={cn(
                  'w-full flex items-center gap-2 px-3 h-9 rounded-md text-sm hover:bg-muted transition-colors',
                  habitId === h.id && 'bg-muted'
                )}
              >
                {habitId === h.id && <Check className="w-4 h-4" />}
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: h.color_hex }}
                  aria-hidden
                />
                <span className="flex-1 text-left truncate">{h.title}</span>
              </button>
            ))
          ) : (
            <div className="px-3 h-9 flex items-center text-sm text-muted-foreground">
              Привычек пока нет
            </div>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}

