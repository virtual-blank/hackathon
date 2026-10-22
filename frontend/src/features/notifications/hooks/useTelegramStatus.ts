import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { useEffect, useRef } from 'react'

type UseTelegramStatusOptions = {
  /**
   * Enable polling when waiting for link completion
   */
  enablePolling?: boolean
  /**
   * Polling interval in milliseconds (default: 3000)
   */
  pollingInterval?: number
  /**
   * Callback when Telegram is successfully connected
   */
  onConnected?: () => void
}

export function useTelegramStatus(options: UseTelegramStatusOptions = {}) {
  const {
    enablePolling = false,
    pollingInterval = 3000,
    onConnected,
  } = options

  const previouslyConnected = useRef<boolean | null>(null)

  const { data, isLoading, isError, error, refetch } = useGetMeApiV1UsersMeGet({
    query: {
      refetchOnWindowFocus: true,
      refetchInterval: enablePolling ? pollingInterval : false,
      refetchIntervalInBackground: false,
    },
  })

  const isConnected =
    data?.telegram_chat_id !== null && data?.telegram_chat_id !== undefined

  // Detect connection change and call onConnected
  useEffect(() => {
    if (
      isConnected &&
      previouslyConnected.current === false &&
      onConnected
    ) {
      onConnected()
    }
    previouslyConnected.current = isConnected
  }, [isConnected, onConnected])

  return {
    isConnected,
    isLoading,
    isError,
    error,
    refetch,
    user: data,
  }
}
