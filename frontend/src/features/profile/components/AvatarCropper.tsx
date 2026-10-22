import { useEffect, useRef, useState, useCallback } from 'react'
import { ZoomIn, ZoomOut } from 'lucide-react'
import { Button } from '@/shared/ui/button'

type CropData = {
  sx: number
  sy: number
  size: number
}

type AvatarCropperProps = {
  src: string
  width: number
  height: number
  onChange: (crop: CropData) => void
}

const V = 256
const MIN_ZOOM = 1
const MAX_ZOOM = 4

export function AvatarCropper({ src, width, height, onChange }: AvatarCropperProps) {
  const [zoom, setZoom] = useState(1)
  const [offset, setOffset] = useState({ x: 0, y: 0 })
  const containerRef = useRef<HTMLDivElement>(null)
  const pointerStartRef = useRef<{ x: number; y: number } | null>(null)
  const offsetStartRef = useRef<{ x: number; y: number } | null>(null)
  const pointersRef = useRef<Map<number, { x: number; y: number }>>(new Map())
  const initialDistanceRef = useRef<number | null>(null)
  const initialZoomRef = useRef<number | null>(null)

  // Reset state when src changes
  /* eslint-disable react-hooks/set-state-in-effect */
  useEffect(() => {
    setZoom(1)
    setOffset({ x: 0, y: 0 })
  }, [src])
  /* eslint-enable react-hooks/set-state-in-effect */

  const baseScale = V / Math.min(width, height)
  const scale = baseScale * zoom
  const dispW = width * scale
  const dispH = height * scale

  const clamp = useCallback(
    (off: { x: number; y: number }): { x: number; y: number } => {
      const maxX = (dispW - V) / 2
      const maxY = (dispH - V) / 2
      return {
        x: Math.min(Math.max(off.x, -maxX), maxX),
        y: Math.min(Math.max(off.y, -maxY), maxY),
      }
    },
    [dispW, dispH]
  )

  const clampedOffset = clamp(offset)

  useEffect(() => {
    const size = V / scale
    const sx = width / 2 - clampedOffset.x / scale - size / 2
    const sy = height / 2 - clampedOffset.y / scale - size / 2
    onChange({ sx, sy, size })
  }, [zoom, clampedOffset.x, clampedOffset.y, width, height, scale, onChange])

  const handleZoomChange = useCallback(
    (newZoom: number) => {
      const clamped = Math.min(Math.max(newZoom, MIN_ZOOM), MAX_ZOOM)
      const newScale = baseScale * clamped
      const oldScale = scale
      const scaledOffset = {
        x: (offset.x * newScale) / oldScale,
        y: (offset.y * newScale) / oldScale,
      }
      setZoom(clamped)
      setOffset(clamp(scaledOffset))
    },
    [baseScale, scale, offset, clamp]
  )

  const handlePointerDown = (e: React.PointerEvent) => {
    const container = containerRef.current
    if (!container) return
    container.setPointerCapture(e.pointerId)
    pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY })

    if (pointersRef.current.size === 1) {
      pointerStartRef.current = { x: e.clientX, y: e.clientY }
      offsetStartRef.current = { ...offset }
    } else if (pointersRef.current.size === 2) {
      const pointers = Array.from(pointersRef.current.values())
      const dx = pointers[1].x - pointers[0].x
      const dy = pointers[1].y - pointers[0].y
      initialDistanceRef.current = Math.sqrt(dx * dx + dy * dy)
      initialZoomRef.current = zoom
      pointerStartRef.current = null
    }
  }

  const handlePointerMove = (e: React.PointerEvent) => {
    pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY })

    if (pointersRef.current.size === 2 && initialDistanceRef.current && initialZoomRef.current) {
      const pointers = Array.from(pointersRef.current.values())
      const dx = pointers[1].x - pointers[0].x
      const dy = pointers[1].y - pointers[0].y
      const dist = Math.sqrt(dx * dx + dy * dy)
      const newZoom = (initialZoomRef.current * dist) / initialDistanceRef.current
      handleZoomChange(newZoom)
    } else if (pointersRef.current.size === 1 && pointerStartRef.current && offsetStartRef.current) {
      const deltaX = e.clientX - pointerStartRef.current.x
      const deltaY = e.clientY - pointerStartRef.current.y
      setOffset(
        clamp({
          x: offsetStartRef.current.x + deltaX,
          y: offsetStartRef.current.y + deltaY,
        })
      )
    }
  }

  const handlePointerUp = (e: React.PointerEvent) => {
    const container = containerRef.current
    if (container) container.releasePointerCapture(e.pointerId)
    pointersRef.current.delete(e.pointerId)
    if (pointersRef.current.size === 0) {
      pointerStartRef.current = null
      offsetStartRef.current = null
      initialDistanceRef.current = null
      initialZoomRef.current = null
    } else if (pointersRef.current.size === 1) {
      const [, pos] = Array.from(pointersRef.current.entries())[0]
      pointerStartRef.current = pos
      offsetStartRef.current = { ...offset }
    }
  }

  useEffect(() => {
    const container = containerRef.current
    if (!container) return
    const handler = (e: WheelEvent) => {
      e.preventDefault()
      handleZoomChange(zoom - e.deltaY * 0.0015)
    }
    container.addEventListener('wheel', handler, { passive: false })
    return () => container.removeEventListener('wheel', handler)
  }, [zoom, handleZoomChange])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      setOffset(clamp({ x: offset.x, y: offset.y - 8 }))
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setOffset(clamp({ x: offset.x, y: offset.y + 8 }))
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      setOffset(clamp({ x: offset.x - 8, y: offset.y }))
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      setOffset(clamp({ x: offset.x + 8, y: offset.y }))
    } else if (e.key === '+' || e.key === '=') {
      e.preventDefault()
      handleZoomChange(zoom + 0.1)
    } else if (e.key === '-') {
      e.preventDefault()
      handleZoomChange(zoom - 0.1)
    }
  }

  const imgLeft = V / 2 + clampedOffset.x - dispW / 2
  const imgTop = V / 2 + clampedOffset.y - dispH / 2

  return (
    <div className="space-y-4">
      <div
        ref={containerRef}
        className="relative w-64 h-64 mx-auto overflow-hidden rounded-2xl bg-muted select-none touch-none cursor-grab active:cursor-grabbing focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        tabIndex={0}
        role="application"
        aria-label="Область кадрирования. Перетаскивайте фото, стрелками двигайте, плюс и минус меняют масштаб"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerCancel={handlePointerUp}
        onKeyDown={handleKeyDown}
      >
        <img
          src={src}
          alt=""
          draggable={false}
          className="absolute max-w-none pointer-events-none select-none"
          style={{
            width: `${dispW}px`,
            height: `${dispH}px`,
            left: `${imgLeft}px`,
            top: `${imgTop}px`,
          }}
        />
        <div
          className="absolute inset-0 pointer-events-none bg-foreground/50"
          style={{
            maskImage: 'radial-gradient(circle at center, transparent calc(50% - 1px), black 50%)',
            WebkitMaskImage: 'radial-gradient(circle at center, transparent calc(50% - 1px), black 50%)',
          }}
        />
        <div className="absolute inset-0 m-auto w-64 h-64 rounded-full ring-1 ring-background/80 pointer-events-none" />
      </div>
      <div className="flex items-center gap-3 w-64 mx-auto">
        <Button type="button" variant="ghost" size="icon" className="shrink-0" aria-label="Уменьшить" onClick={() => handleZoomChange(zoom - 0.25)}>
          <ZoomOut className="w-4 h-4" />
        </Button>
        <input type="range" min={MIN_ZOOM} max={MAX_ZOOM} step={0.01} value={zoom} onChange={(e) => handleZoomChange(parseFloat(e.target.value))} className="flex-1 accent-foreground" aria-label="Масштаб" />
        <Button type="button" variant="ghost" size="icon" className="shrink-0" aria-label="Увеличить" onClick={() => handleZoomChange(zoom + 0.25)}>
          <ZoomIn className="w-4 h-4" />
        </Button>
      </div>
      <p className="text-center text-[13px] text-muted-foreground">Перетащите фото и измените масштаб</p>
    </div>
  )
}
