import { useMemo } from 'react'
import { useGetFeedApiV1FeedGet } from '@/api/generated/👁‍🗨-feed/👁‍🗨-feed'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { getTodayDate } from '@/features/habits/lib/utils'

export type FriendActivity = {
  lastActiveDate: string | null
  totalLogs: number
  activeToday: boolean
}

export function useFriendsActivity() {
  const { data: me } = useGetMeApiV1UsersMeGet()
  const { data: feed, isLoading, isError } = useGetFeedApiV1FeedGet(
    { limit: 100, offset: 0 },
    {
      query: {
        staleTime: 30_000,
      },
    }
  )

  const activityMap = useMemo(() => {
    const map = new Map<string, FriendActivity>()

    if (!feed || !me) return map

    const todayDate = getTodayDate(me.timezone || 'UTC')

    // Filter out current user's own feed
    const friendsFeed = feed.filter((item) => item.creator.id !== me.id)

    // Group by creator.id
    for (const item of friendsFeed) {
      const creatorId = item.creator.id
      const existing = map.get(creatorId)

      // Find max completed_date
      const dates = item.habit_logs.map((log) => log.completed_date)
      const maxDate = dates.length > 0 ? dates.sort().reverse()[0] : null

      const hasToday = dates.includes(todayDate)

      if (existing) {
        // Update existing
        const newMaxDate =
          maxDate &&
          (!existing.lastActiveDate || maxDate > existing.lastActiveDate)
            ? maxDate
            : existing.lastActiveDate

        map.set(creatorId, {
          lastActiveDate: newMaxDate,
          totalLogs: existing.totalLogs + item.total_logs_count,
          activeToday: existing.activeToday || hasToday,
        })
      } else {
        // Create new
        map.set(creatorId, {
          lastActiveDate: maxDate,
          totalLogs: item.total_logs_count,
          activeToday: hasToday,
        })
      }
    }

    return map
  }, [feed, me])

  return {
    activityMap,
    isLoading,
    isError,
  }
}
