import { Download, Loader2 } from 'lucide-react'
import { Button } from '@/shared/ui/button'
import { getExportHabitsSummaryApiV1ExportsHabitsSummaryCsvGetUrl } from '@/api/generated/📥-exports/📥-exports'
import { ExportDelimiter } from '@/api/generated/model'
import { useCsvDownload } from '../hooks/useCsvDownload'
import { SettingsSection, SettingsRow } from './SettingsSection'
import { todayIso } from '../lib/dates'

type Props = {
  delimiter: ExportDelimiter
  timezone: string
}

export function SummaryExportCard({ delimiter, timezone }: Props) {
  const { mutate, isPending } = useCsvDownload()

  const handleDownload = () => {
    const url = getExportHabitsSummaryApiV1ExportsHabitsSummaryCsvGetUrl({ delimiter })
    const today = todayIso(timezone)
    mutate({ url, fallbackName: `habits-summary-${today}.csv` })
  }

  return (
    <SettingsSection
      title="Сводка по привычкам"
      description="Количество дней, процент выполнения, серии, статусы заброшенности и реакции друзей по всем вашим привычкам"
    >
      <SettingsRow label="Скачать сводную таблицу" isLast>
        <Button
          onClick={handleDownload}
          disabled={isPending}
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
      </SettingsRow>
    </SettingsSection>
  )
}
