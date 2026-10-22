import { customFetchBlob } from '@/api/mutator'

export async function downloadCsv(
  url: string,
  fallbackName: string
): Promise<{ rows: number; bytes: number } | null> {
  const { blob, filename } = await customFetchBlob(url)

  // Count rows (minus BOM and header)
  const text = await blob.text()
  const cleanText = text.replace(/^\uFEFF/, '')
  const lines = cleanText.split('\n').filter((line) => line.trim() !== '')
  const rows = Math.max(0, lines.length - 1) // exclude header

  if (rows === 0) return null

  // Trigger download with original BOM-preserved blob
  const objectURL = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectURL
  a.download = filename ?? fallbackName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(objectURL), 1000)

  return { rows, bytes: blob.size }
}
