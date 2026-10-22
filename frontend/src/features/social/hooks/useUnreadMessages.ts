import { useQueries } from '@tanstack/react-query'
import { useGetFriendsApiV1FriendsGet } from '@/api/generated/🤝-friends/🤝-friends'
import { getGetHistoryApiV1SocialMessagesPeerIdGetQueryOptions } from '@/api/generated/💬-social/💬-social'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { UNREAD_CHECK_PARAMS } from '../lib/constants'
import type { MessageOutputSchema } from '@/api/generated/model'

export function useUnreadMessages() {
  const { data: me } = useGetMeApiV1UsersMeGet()
  const { data: friends } = useGetFriendsApiV1FriendsGet({ limit: 100, offset: 0 })

  const queries = useQueries({
    queries: (friends ?? []).map((friend) =>
      getGetHistoryApiV1SocialMessagesPeerIdGetQueryOptions(friend.id, UNREAD_CHECK_PARAMS, {
        query: {
          retry: 1,
          staleTime: 30_000,
          refetchInterval: 60_000,
          refetchIntervalInBackground: true,
        },
      })
    ),
  })

  const hasUnreadMessages =
    !!me &&
    queries.some((q) =>
      ((q.data as MessageOutputSchema[] | undefined) ?? []).some(
        (m) => m.receiver_id === me.id && !m.is_read
      )
    )

  return { hasUnreadMessages }
}
