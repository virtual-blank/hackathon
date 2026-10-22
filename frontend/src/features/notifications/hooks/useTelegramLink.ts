import { useGenerateTelegramLinkApiV1TelegramLinkPost } from '@/api/generated/📱-telegram/📱-telegram'
import { useState } from 'react'
import { toast } from 'sonner'
import { getErrorMessage } from '@/shared/lib/errors'

type UseTelegramLinkReturn = {
  generateAndOpenLink: () => void
  isPending: boolean
  isWaitingForConnection: boolean
  fallbackUrl: string | null
  clearFallback: () => void
}

export function useTelegramLink(
  onLinkOpened?: () => void
): UseTelegramLinkReturn {
  const [isWaitingForConnection, setIsWaitingForConnection] = useState(false)
  const [fallbackUrl, setFallbackUrl] = useState<string | null>(null)

  const { mutate: generateLink, isPending } =
    useGenerateTelegramLinkApiV1TelegramLinkPost({
      mutation: {
        onSuccess: (data) => {
          const { url } = data

          // Try to open in new tab
          const newWindow = window.open(url, '_blank', 'noopener,noreferrer')

          if (newWindow) {
            // Successfully opened
            setIsWaitingForConnection(true)
            onLinkOpened?.()
          } else {
            // Popup blocked - show fallback
            setFallbackUrl(url)
            toast.error('Всплывающее окно заблокировано. Откройте ссылку вручную.')
          }
        },
        onError: (error) => {
          const message = getErrorMessage(error)
          toast.error(message || 'Не удалось создать ссылку')
        },
      },
    })

  const generateAndOpenLink = () => {
    setFallbackUrl(null)
    generateLink()
  }

  const clearFallback = () => {
    setFallbackUrl(null)
  }

  return {
    generateAndOpenLink,
    isPending,
    isWaitingForConnection,
    fallbackUrl,
    clearFallback,
  }
}
