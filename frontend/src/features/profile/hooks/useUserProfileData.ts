import { useGetHabitsApiV1HabitsGet } from '@/api/generated/🏃-habits/🏃-habits'
import { useGetDashboardApiV1AnalyticsDashboardGet } from '@/api/generated/📊-analytics/📊-analytics'
import { useGetFriendsApiV1FriendsGet, useGetRequestsApiV1FriendsRequestsGet } from '@/api/generated/🤝-friends/🤝-friends'
import { useLocation } from 'react-router-dom'
import type { HabitOutputSchema, DashboardOutputSchema } from '@/api/generated/model'

type UserIdentity = {
  id: string
  username: string
  pfp_url: string
}

type UserProfileData = {
  userIdentity: UserIdentity | null
  habits: HabitOutputSchema[] | undefined
  dashboard: DashboardOutputSchema | undefined
  isBlocked: boolean
  isNotFound: boolean
  isLoading: boolean
  isError: boolean
  refetch: () => void
}

export function useUserProfileData(userId: string | undefined): UserProfileData {
  const location = useLocation()

  // Try to get identity from location state (passed from navigation)
  const stateIdentity = location.state as UserIdentity | null

  // Load habits and dashboard for the target user
  const habitsQuery = useGetHabitsApiV1HabitsGet(
    { target_user_id: userId!, limit: 100 },
    { query: { enabled: !!userId } }
  )
  const dashboardQuery = useGetDashboardApiV1AnalyticsDashboardGet(
    {
      target_user_id: userId!,
      activity_days: 182,
    },
    { query: { enabled: !!userId } }
  )

  // Load friends and requests to find user identity if not in state
  const friendsQuery = useGetFriendsApiV1FriendsGet({ limit: 100 }, { query: { enabled: !stateIdentity } })
  const requestsQuery = useGetRequestsApiV1FriendsRequestsGet(undefined, { query: { enabled: !stateIdentity } })

  // Determine user identity
  let userIdentity: UserIdentity | null = stateIdentity

  if (!userIdentity && !friendsQuery.isLoading && !requestsQuery.isLoading) {
    // Search in friends
    const friend = friendsQuery.data?.find((f) => f.id === userId)
    if (friend) {
      userIdentity = friend
    } else {
      // Search in incoming/outgoing requests
      const incoming = requestsQuery.data?.incoming.find((r) => r.id === userId)
      const outgoing = requestsQuery.data?.outgoing.find((r) => r.id === userId)
      userIdentity = incoming || outgoing || null
    }
  }

  // Check for blocked/not found status
  // Backend returns 403 when blocked by target user (dashboard)
  // Backend returns 400 when blocked by target user (habits)
  // Backend returns 404 when user not found
  const getErrorStatus = (error: unknown): number | undefined => {
    if (error && typeof error === 'object' && 'response' in error) {
      const response = (error as { response?: { status?: number } }).response
      return response?.status
    }
    return undefined
  }

  const isBlocked =
    (habitsQuery.isError && getErrorStatus(habitsQuery.error) === 400) ||
    (dashboardQuery.isError && getErrorStatus(dashboardQuery.error) === 403)
  const isNotFound =
    (habitsQuery.isError && getErrorStatus(habitsQuery.error) === 404) ||
    (dashboardQuery.isError && getErrorStatus(dashboardQuery.error) === 404)

  const isLoading =
    habitsQuery.isLoading ||
    dashboardQuery.isLoading ||
    (friendsQuery.isLoading && !stateIdentity) ||
    (requestsQuery.isLoading && !stateIdentity)

  const isError = (habitsQuery.isError && !isBlocked && !isNotFound) || dashboardQuery.isError

  // Filter out private habits (critical privacy check)
  const visibleHabits = (habitsQuery.data || []).filter((h) => h.visibility !== 'private')

  // Log if private habits leaked (backend bug)
  if (habitsQuery.data && habitsQuery.data.some((h) => h.visibility === 'private')) {
    console.error(
      '[PRIVACY LEAK] Private habits received from backend for user',
      userId,
      'This is a backend bug!'
    )
  }

  const refetch = () => {
    habitsQuery.refetch()
    dashboardQuery.refetch()
  }

  return {
    userIdentity: !isBlocked && !isNotFound ? userIdentity : null,
    habits: visibleHabits,
    dashboard: dashboardQuery.data,
    isBlocked,
    isNotFound,
    isLoading,
    isError,
    refetch,
  }
}
