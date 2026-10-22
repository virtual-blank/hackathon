import { useState, useMemo } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  useGetMeApiV1UsersMeGet,
  useEditProfileApiV1UsersMePatch,
  getGetMeApiV1UsersMeGetQueryKey,
} from '@/api/generated/👤-users/👤-users'
import { TimezoneEnum } from '@/api/generated/model/timezoneEnum'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { ChevronsUpDown, Search } from 'lucide-react'
import { toast } from 'sonner'
import { SettingsSection, SettingsRow } from './SettingsSection'
import { cn } from '@/shared/lib/utils'

type TimezoneOption = { tz: string; offset: string; label: string; offsetMinutes: number }

function getTimezones(): TimezoneOption[] {
  const tzs = Object.values(TimezoneEnum)
  return tzs.map((tz) => {
    const parts = new Intl.DateTimeFormat('en', {
      timeZone: tz,
      timeZoneName: 'longOffset',
    }).formatToParts(new Date())
    const offsetPart = parts.find((p) => p.type === 'timeZoneName')?.value || 'GMT'
    const offsetMatch = /GMT([+-]?)(\d+):?(\d*)/.exec(offsetPart)
    let offsetMinutes = 0
    if (offsetMatch) {
      const sign = offsetMatch[1] === '-' ? -1 : 1
      const hours = parseInt(offsetMatch[2] || '0', 10)
      const minutes = parseInt(offsetMatch[3] || '0', 10)
      offsetMinutes = sign * (hours * 60 + minutes)
    }
    const offsetStr = offsetPart.replace(':00', '').replace(':30', ':30')
    const labelParts = new Intl.DateTimeFormat('ru-RU', {
      timeZone: tz,
      timeZoneName: 'longGeneric',
    }).formatToParts(new Date())
    let label = labelParts.find((p) => p.type === 'timeZoneName')?.value || ''
    if (!label || label === tz) {
      const city = tz.split('/').pop()?.replace(/_/g, ' ') || tz
      label = city
    }
    return { tz, offset: offsetStr, label, offsetMinutes }
  }).sort((a, b) => a.offsetMinutes - b.offsetMinutes || a.label.localeCompare(b.label, 'ru'))
}

export function RegionSection() {
  const queryClient = useQueryClient()
  const { data: me } = useGetMeApiV1UsersMeGet()
  const { mutate: editProfile } = useEditProfileApiV1UsersMePatch()
  const [popoverOpen, setPopoverOpen] = useState(false)
  const [search, setSearch] = useState('')
  const timezones = useMemo(() => getTimezones(), [])
  const filtered = useMemo(
    () =>
      timezones.filter(
        (opt) =>
          opt.label.toLowerCase().includes(search.toLowerCase()) ||
          opt.tz.toLowerCase().includes(search.toLowerCase()) ||
          opt.offset.toLowerCase().includes(search.toLowerCase())
      ),
    [timezones, search]
  )

  const handleSelect = (tz: string) => {
    editProfile(
      { data: { timezone: tz as typeof TimezoneEnum[keyof typeof TimezoneEnum] } },
      {
        onSuccess: (user) => {
          queryClient.setQueryData(getGetMeApiV1UsersMeGetQueryKey(), user)
          queryClient.invalidateQueries()
          toast.success('Часовой пояс обновлён')
          setPopoverOpen(false)
        },
        onError: () => toast.error('Не удалось изменить часовой пояс'),
      }
    )
  }

  const handleAutoDetect = () => {
    const detected = Intl.DateTimeFormat().resolvedOptions().timeZone
    if (Object.values(TimezoneEnum).includes(detected as typeof TimezoneEnum[keyof typeof TimezoneEnum])) {
      handleSelect(detected)
    } else {
      toast.error('Ваш часовой пояс недоступен, выберите из списка')
    }
  }

  const current = timezones.find((opt) => opt.tz === me?.timezone)

  return (
    <SettingsSection title="Регион" description="От часового пояса зависит, когда начинается новый день для ваших привычек">
      <SettingsRow label="Часовой пояс" isLast>
        <Popover open={popoverOpen} onOpenChange={setPopoverOpen}>
          <PopoverTrigger asChild>
            <Button variant="ghost" size="sm" className="gap-2">
              {current ? `${current.label} (${current.offset})` : me?.timezone || 'Выбрать'}
              <ChevronsUpDown className="w-4 h-4" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80 p-2" align="end">
            <div className="space-y-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Поиск..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8 h-9"
                />
              </div>
              <Button variant="outline" size="sm" onClick={handleAutoDetect} className="w-full">
                Определить автоматически
              </Button>
              <div className="max-h-80 overflow-y-auto" role="listbox">
                {filtered.map((opt) => (
                  <button
                    key={opt.tz}
                    onClick={() => handleSelect(opt.tz)}
                    className={cn(
                      'w-full text-left px-2 py-2 text-sm rounded hover:bg-muted',
                      opt.tz === me?.timezone && 'bg-muted font-medium'
                    )}
                    role="option"
                    aria-selected={opt.tz === me?.timezone}
                  >
                    <div>{opt.label}</div>
                    <div className="text-xs text-muted-foreground">{opt.offset}</div>
                  </button>
                ))}
                {filtered.length === 0 && (
                  <div className="px-2 py-4 text-sm text-muted-foreground text-center">Не найдено</div>
                )}
              </div>
            </div>
          </PopoverContent>
        </Popover>
      </SettingsRow>
    </SettingsSection>
  )
}
