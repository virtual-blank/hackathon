import { useQueries } from '@tanstack/react-query'
import { getGetHistoryApiV1SocialMessagesPeerIdGetQueryOptions } from '@/api/generated/💬-social/💬-social'
import { CHAT_PREVIEW_PARAMS } from '../lib/constants'
import type { FriendSchema, MessageOutputSchema } from '@/api/generated/model'

export type ChatPeerWithPreview = {
  friend: FriendSchema
  lastMessage: MessageOutputSchema | null
  isLoading: boolean
  isError: boolean
}

export function useChatPeers(friends: FriendSchema[] | undefined) {
  const previewQueries = useQueries({
    queries: (friends || []).map((friend) =>
      getGetHistoryApiV1SocialMessagesPeerIdGetQueryOptions(friend.id, CHAT_PREVIEW_PARAMS, {
        query: {
          retry: 1,
          staleTime: 30_000,
        },
      })
    ),
  })

  const peers: ChatPeerWithPreview[] = (friends || []).map((friend, index) => {
    const query = previewQueries[index]
    const messages = query.data || []
    const lastMessage =
      messages.length > 0
        ? messages.reduce((latest, msg) =>
            new Date(msg.created_at) > new Date(latest.created_at) ? msg : latest
          )
        : null

    return {
      friend,
      lastMessage,
      isLoading: query.isLoading,
      isError: query.isError,
    }
  })

  // Сортировка: новые сообщения сверху, без сообщений внизу по алфавиту
  const sorted = [...peers].sort((a, b) => {
    if (a.lastMessage && b.lastMessage) {
      return (
        new Date(b.lastMessage.created_at).getTime() -
        new Date(a.lastMessage.created_at).getTime()
      )
    }
    if (a.lastMessage && !b.lastMessage) return -1
    if (!a.lastMessage && b.lastMessage) return 1
    return a.friend.username.localeCompare(b.friend.username, 'ru')
  })

  return sorted
}
