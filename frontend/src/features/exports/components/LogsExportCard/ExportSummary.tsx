import { formatDateDMY } from '../../lib/dates'

type Props = {
  habitTitle: string
  dateFrom: string | undefined
  dateTo: string | undefined
}

export function ExportSummary({ habitTitle, dateFrom, dateTo }: Props) {
  const habitLabel = habitTitle ? `«${habitTitle}»` : 'все привычки'

  let periodLabel = 'за всё время'
  if (dateFrom && dateTo) {
    periodLabel = `${formatDateDMY(dateFrom)} – ${formatDateDMY(dateTo)}`
  } else if (dateFrom) {
    periodLabel = `с ${formatDateDMY(dateFrom)}`
  } else if (dateTo) {
    periodLabel = `до ${formatDateDMY(dateTo)}`
  }

  return (
    <p className="text-[13px] text-muted-foreground">
      Будет выгружено: {habitLabel} · {periodLabel}
    </p>
  )
}
