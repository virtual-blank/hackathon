import { useState, useMemo } from 'react'
import { Download, Loader2 } from 'lucide-react'
import { Button } from '@/shared/ui/button'
import { getExportHabitLogsApiV1ExportsHabitsLogsCsvGetUrl } from '@/api/generated/📥-exports/📥-exports'
import { ExportDelimiter } from '@/api/generated/model'
import { useCsvDownload } from '../../hooks/useCsvDownload'
import { SettingsSection, SettingsRow } from '../SettingsSection'
import { todayIso } from '../../lib/dates'
import { safeName } from '../../lib/filename'
import { PeriodPicker } from './PeriodPicker'
import { HabitPicker } from './HabitPicker'
import { ExportSummary } from './ExportSummary'

type Props = {
  delimiter: ExportDelimiter
  timezone: string
  habitsLoading: boolean
}

export function LogsExportCard({ delimiter, timezone, habitsLoading }: Props) {
  const today = todayIso(timezone)

  const [periodType, setPeriodType] = useState<string>('all')
  const [customFrom, setCustomFrom] = useState('')
  const [customTo, setCustomTo] = useState('')
  const [habitId, setHabitId] = useState<string | undefined>(undefined)
  const [habitTitle, setHabitTitle] = useState<string>('')

  const { mutate, isPending } = useCsvDownload()

  // Compute date_from / date_to based on period type
  const { dateFrom, dateTo } = useMemo(() => {
    if (periodType === 'custom') {
      return { dateFrom: customFrom || undefined, dateTo: customTo || undefined }
    }
    if (periodType === 'all') return { dateFrom: undefined, dateTo: undefined }
    // period presets are computed inside PeriodPicker and returned as custom type
    return { dateFrom: undefined, dateTo: undefined }
  }, [periodType, customFrom, customTo])

  const validationError = useMemo(() => {
    if (periodType === 'custom' && customFrom && customTo && customFrom > customTo) {
      return 'Начало периода позже конца'
    }
    return null
  }, [periodType, customFrom, customTo])

  const handleDownload = () => {
    const params: {
      delimiter: ExportDelimiter
      date_from?: string
      date_to?: string
      habit_id?: string
    } = { delimiter }

    if (dateFrom) params.date_from = dateFrom
    if (dateTo) params.date_to = dateTo
    if (habitId) params.habit_id = habitId

    const url = getExportHabitLogsApiV1ExportsHabitsLogsCsvGetUrl(params)
    const habit = habitTitle ? safeName(habitTitle) : 'all-habits'
    const from = dateFrom || 'start'
    const to = dateTo || today
    mutate({ url, fallbackName: `${habit}_logs_${from}_${to}.csv` })
  }

  return (
    <SettingsSection
      title="Журнал выполнений"
      description="Все отметки о выполнении привычек по датам"
    >
      <SettingsRow label="Период">
        <PeriodPicker
          value={periodType}
          onChange={setPeriodType}
          today={today}
          customFrom={customFrom}
          customTo={customTo}
          onCustomFromChange={setCustomFrom}
          onCustomToChange={setCustomTo}
        />
      </SettingsRow>

      <SettingsRow label="Привычка">
        <HabitPicker
          habitId={habitId}
          habitTitle={habitTitle}
          onSelect={(id, title) => {
            setHabitId(id)
            setHabitTitle(title)
          }}
          loading={habitsLoading}
        />
      </SettingsRow>

      <SettingsRow label="" isLast>
        <div className="flex flex-col items-end gap-3 w-full">
          <ExportSummary
            habitTitle={habitTitle}
            dateFrom={dateFrom}
            dateTo={dateTo}
          />
          {validationError && (
            <p className="text-sm text-destructive">{validationError}</p>
          )}
          <Button
            onClick={handleDownload}
            disabled={isPending || !!validationError}
            size="sm"
            className="gap-2"
          >
            {isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Готовим файл…
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Скачать CSV
              </>
            )}
          </Button>
        </div>
      </SettingsRow>
    </SettingsSection>
  )
}
