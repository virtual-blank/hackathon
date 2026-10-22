import { Input } from '@/shared/ui/input'

type Props = {
  from: string
  to: string
  onFromChange: (v: string) => void
  onToChange: (v: string) => void
  maxDate: string
}

export function CustomDateRange({ from, to, onFromChange, onToChange, maxDate }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3">
      <div>
        <label htmlFor="date-from" className="block text-sm font-medium mb-1">
          С
        </label>
        <Input
          id="date-from"
          type="date"
          value={from}
          onChange={(e) => onFromChange(e.target.value)}
          max={maxDate}
          className="[color-scheme:light] dark:[color-scheme:dark]"
        />
      </div>
      <div>
        <label htmlFor="date-to" className="block text-sm font-medium mb-1">
          По
        </label>
        <Input
          id="date-to"
          type="date"
          value={to}
          onChange={(e) => onToChange(e.target.value)}
          max={maxDate}
          className="[color-scheme:light] dark:[color-scheme:dark]"
        />
      </div>
    </div>
  )
}
