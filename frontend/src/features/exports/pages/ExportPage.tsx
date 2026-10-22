import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { useGetHabitsApiV1HabitsGet } from '@/api/generated/🏃-habits/🏃-habits'
import { Skeleton } from '@/shared/ui/skeleton'
import { useExportDelimiter } from '../hooks/useExportDelimiter'
import { DelimiterToggle } from '../components/DelimiterToggle'
import { SummaryExportCard } from '../components/SummaryExportCard'
import { LogsExportCard } from '../components/LogsExportCard'

export function ExportPage() {
  const { data: me, isLoading: meLoading } = useGetMeApiV1UsersMeGet()
  const { isLoading: habitsLoading } = useGetHabitsApiV1HabitsGet({ limit: 100, offset: 0 })
  const [delimiter, setDelimiter] = useExportDelimiter()

  if (meLoading) {
    return (
      <div className="max-w-[720px] mx-auto px-4 lg:px-8 py-8 space-y-10">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-32 w-full rounded-2xl" />
        <Skeleton className="h-48 w-full rounded-2xl" />
      </div>
    )
  }

  if (!me) return null

  return (
    <div className="max-w-[720px] mx-auto px-4 lg:px-8 py-8 space-y-10">
      <div>
        <h1 className="font-serif text-[32px] font-semibold leading-tight">
          Экспорт данных
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Скачайте свои данные в CSV, чтобы открыть их в Excel или Google Таблицах
        </p>
      </div>

      <DelimiterToggle value={delimiter} onChange={setDelimiter} />

      <SummaryExportCard delimiter={delimiter} timezone={me.timezone} />

      <LogsExportCard
        delimiter={delimiter}
        timezone={me.timezone}
        habitsLoading={habitsLoading}
      />

      <p className="text-[13px] text-muted-foreground leading-relaxed">
        Как открыть: в Excel дважды кликните по файлу (разделитель « ; » для русской версии),
        в Google Таблицах: Файл → Импорт → Загрузка. Файл в кодировке UTF-8, кириллица отображается корректно.
      </p>
    </div>
  )
}

