import { useState, useEffect } from 'react'
import { ExportDelimiter } from '@/api/generated/model'

const KEY = 'export-delimiter-v1'

export function useExportDelimiter(): [ExportDelimiter, (d: ExportDelimiter) => void] {
  const [delimiter, setDelimiterState] = useState<ExportDelimiter>(ExportDelimiter[';'])

  useEffect(() => {
    try {
      const stored = localStorage.getItem(KEY)
      if (stored === ',' || stored === ';') {
        setDelimiterState(stored as ExportDelimiter)
      }
    } catch {
      // ignore
    }
  }, [])

  const setDelimiter = (d: ExportDelimiter) => {
    setDelimiterState(d)
    try {
      localStorage.setItem(KEY, d)
    } catch {
      // ignore
    }
  }

  return [delimiter, setDelimiter]
}
