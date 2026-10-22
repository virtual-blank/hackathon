export async function processImageFile(
  file: File,
  crop?: { sx: number; sy: number; size: number }
): Promise<Blob | null> {
  try {
    const bitmap = await createImageBitmap(file)
    const size = 512
    const canvas = document.createElement('canvas')
    canvas.width = size
    canvas.height = size
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('Canvas context not available')

    let sx: number, sy: number, sw: number, sh: number

    if (crop) {
      // Use crop data from the cropper
      sx = crop.sx
      sy = crop.sy
      sw = crop.size
      sh = crop.size
    } else {
      // Fallback centre crop
      const scale = Math.max(size / bitmap.width, size / bitmap.height)
      sw = size / scale
      sh = size / scale
      sx = (bitmap.width - sw) / 2
      sy = (bitmap.height - sh) / 2
    }

    ctx.drawImage(bitmap, sx, sy, sw, sh, 0, 0, size, size)

    return new Promise((resolve) => {
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            canvas.toBlob(resolve, 'image/jpeg', 0.9)
          } else {
            resolve(blob)
          }
        },
        'image/webp',
        0.9
      )
    })
  } catch {
    return null
  }
}
