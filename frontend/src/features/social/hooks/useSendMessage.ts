import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getGetHistoryApiV1SocialMessagesPeerIdGetQueryKey } from '@/api/generated/💬-social/💬-social'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { CHAT_HISTORY_PARAMS } from '../lib/constants'
import type { MessageOutputSchema } from '@/api/generated/model'

export function useSendMessage(socketRef: React.RefObject<WebSocket | null>) {
  const queryClient = useQueryClient()
  const { data: currentUser } = useGetMeApiV1UsersMeGet()
  const [isPending, setIsPending] = useState(false)

  const sendMessage = async (receiverId: string, content: string) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      throw new Error('WebSocket не подключен')
    }

    if (!currentUser) {
      throw new Error('Пользователь не авторизован')
    }

    const queryKey = getGetHistoryApiV1SocialMessagesPeerIdGetQueryKey(
      receiverId,
      CHAT_HISTORY_PARAMS
    )

    const optimisticMessage: MessageOutputSchema = {
      id: `temp-${Date.now()}`,
      sender_id: currentUser.id,
      receiver_id: receiverId,
      content,
      is_read: false,
      read_at: null,
      created_at: new Date().toISOString(),
    }

    // Optimistically add message to cache
    queryClient.setQueryData<MessageOutputSchema[]>(queryKey, (old) => [
      ...(old || []),
      optimisticMessage,
    ])

    setIsPending(true)

    try {
      socketRef.current.send(
        JSON.stringify({
          type: 'message',
          receiver_id: receiverId,
          content,
        })
      )
      // WebSocket will handle the response and update the cache
    } catch (error) {
      // Rollback on error
      queryClient.setQueryData<MessageOutputSchema[]>(queryKey, (old) =>
        old?.filter((msg) => msg.id !== optimisticMessage.id)
      )
      throw error
    } finally {
      setIsPending(false)
    }
  }

  return {
    sendMessage,
    isPending,
  }
}
