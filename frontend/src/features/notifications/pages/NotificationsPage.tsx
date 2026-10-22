import { useTelegramStatus } from '../hooks/useTelegramStatus'
import { useTelegramLink } from '../hooks/useTelegramLink'
import { TelegramStatusCard } from '../components/TelegramStatusCard'
import { TelegramStatusSkeleton } from '../components/TelegramStatusSkeleton'
import { ErrorState } from '@/shared/components/ErrorState'
import { getErrorMessage } from '@/shared/lib/errors'
import { toast } from 'sonner'
import { useState, useCallback, useEffect, useRef } from 'react'

const POLLING_TIMEOUT_MS = 60000 // 60 seconds

export function NotificationsPage() {
  const [enablePolling, setEnablePolling] = useState(false)
  const pollingStartTime = useRef<number | null>(null)

  const handleConnected = useCallback(() => {
    toast.success('Telegram подключён')
    setEnablePolling(false)
    pollingStartTime.current = null
  }, [])

  const {
    isConnected,
    isLoading,
    isError,
    error,
    refetch,
  } = useTelegramStatus({
    enablePolling,
    onConnected: handleConnected,
  })

  const handleLinkOpened = useCallback(() => {
    setEnablePolling(true)
    pollingStartTime.current = Date.now()
  }, [])

  const {
    generateAndOpenLink,
    isPending,
    isWaitingForConnection,
    fallbackUrl,
    clearFallback,
  } = useTelegramLink(handleLinkOpened)

  // Stop polling after timeout
  useEffect(() => {
    if (!enablePolling || isConnected) {
      return
    }

    const timeoutCheck = setInterval(() => {
      if (
        pollingStartTime.current !== null &&
        Date.now() - pollingStartTime.current > POLLING_TIMEOUT_MS
      ) {
        setEnablePolling(false)
        pollingStartTime.current = null
      }
    }, 1000)

    return () => clearInterval(timeoutCheck)
  }, [enablePolling, isConnected])

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8">
        <h1 className="mb-8 font-serif text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
          Уведомления
        </h1>
        <TelegramStatusSkeleton />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8">
        <h1 className="mb-8 font-serif text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
          Уведомления
        </h1>
        <ErrorState
          message={getErrorMessage(error) || 'Не удалось загрузить данные'}
          onRetry={refetch}
        />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-8 font-serif text-3xl font-semibold tracking-tight text-foreground md:text-4xl">
        Уведомления
      </h1>
      <TelegramStatusCard
        isConnected={isConnected}
        onConnect={generateAndOpenLink}
        isPending={isPending || isWaitingForConnection}
        fallbackUrl={fallbackUrl}
        onClearFallback={clearFallback}
      />
    </div>
  )
}
