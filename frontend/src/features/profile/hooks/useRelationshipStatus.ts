import { useGetFriendsApiV1FriendsGet, useGetRequestsApiV1FriendsRequestsGet } from '@/api/generated/🤝-friends/🤝-friends'

type RelationshipStatus = {
  isFriend: boolean
  isIncomingRequest: boolean
  isOutgoingRequest: boolean
  isPending: boolean
}

export function useRelationshipStatus(userId: string | undefined): RelationshipStatus {
  // Load friends with pagination (up to 100)
  const friendsQuery = useGetFriendsApiV1FriendsGet({ limit: 100, offset: 0 })
  const requestsQuery = useGetRequestsApiV1FriendsRequestsGet()

  const friends = friendsQuery.data || []
  const requests = requestsQuery.data

  const isPending = friendsQuery.isLoading || requestsQuery.isLoading

  if (!userId || isPending) {
    return {
      isFriend: false,
      isIncomingRequest: false,
      isOutgoingRequest: false,
      isPending,
    }
  }

  const isFriend = friends.some((f) => f.id === userId)
  const isIncomingRequest = (requests?.incoming || []).some((r) => r.id === userId)
  const isOutgoingRequest = (requests?.outgoing || []).some((r) => r.id === userId)

  return {
    isFriend,
    isIncomingRequest,
    isOutgoingRequest,
    isPending,
  }
}
