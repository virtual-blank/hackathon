import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { downloadCsv } from '../lib/download'
import { pluralize } from '@/shared/lib/pluralize'

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} байт`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} КБ`
  return `${(bytes / (1024 * 1024)).toFixed(1)} МБ`
}

function getHttpStatus(msg: string): number | null {
  const m = /^HTTP (\d+)/.exec(msg)
  return m ? parseInt(m[1], 10) : null
}

export function useCsvDownload() {
  return useMutation({
    mutationFn: ({ url, fallbackName }: { url: string; fallbackName: string }) =>
      downloadCsv(url, fallbackName),
    onSuccess: (result, { fallbackName }) => {
      if (result === null) {
        // No data rows
        if (fallbackName.startsWith('habits-summary')) {
          toast.info('У вас пока нет привычек для выгрузки')
        } else {
          toast.info('За выбранные параметры отметок нет')
        }
      } else {
        const { rows, bytes } = result
        toast.success(
          `Файл скачан: ${rows} ${pluralize(rows, 'строка', 'строки', 'строк')}, ${formatSize(bytes)}`
        )
      }
    },
    onError: (error: Error) => {
      const status = getHttpStatus(error.message)
      if (status === 422) {
        toast.error('Проверьте параметры экспорта')
      } else {
        toast.error('Не удалось скачать файл. Попробуйте ещё раз')
      }
    },
  })
}
