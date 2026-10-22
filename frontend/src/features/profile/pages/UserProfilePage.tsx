import { Navigate, useParams } from 'react-router-dom'
import { motion } from 'motion/react'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { useUserProfileData } from '../hooks/useUserProfileData'
import { useRelationshipStatus } from '../hooks/useRelationshipStatus'
import { getBrightestHabit } from '../lib/profile-helpers'
import { ErrorState } from '@/shared/components/ErrorState'
import { EmptyState } from '@/shared/components/EmptyState'
import { ProfileBlockedState } from '../components/ProfileBlockedState'
import { UserProfileHero } from '../components/UserProfileHero'
import { ProfileHeroSkeleton } from '../components/ProfileHeroSkeleton'
import { ProfileHighlights } from '../components/ProfileHighlights'
import { ProfileHighlightsSkeleton } from '../components/ProfileHighlightsSkeleton'
import { ProfileActivity } from '../components/ProfileActivity'
import { ProfileActivitySkeleton } from '../components/ProfileActivitySkeleton'
import { ProfileHabitsShowcase } from '../components/ProfileHabitsShowcase'
import { ProfileHabitsShowcaseSkeleton } from '../components/ProfileHabitsShowcaseSkeleton'
import type { HabitLogOutputSchema } from '@/api/generated/model'
import defaultPfp from '@/assets/defaults/default-pfp.webp'

export function UserProfilePage() {
  const { userId } = useParams<{ userId: string }>()
  const { data: me } = useGetMeApiV1UsersMeGet()

  const {
    userIdentity,
    habits,
    dashboard,
    isBlocked,
    isNotFound,
    isLoading,
    isError,
    refetch,
  } = useUserProfileData(userId)

  const { isFriend, isIncomingRequest, isOutgoingRequest, isPending: relationshipPending } =
    useRelationshipStatus(userId)

  // Redirect to own profile if viewing self
  if (me && userId === me.id) {
    return <Navigate to="/profile" replace />
  }

  if (!userId) {
    return <EmptyState title="Пользователь не найден" />
  }

  // Handle blocked/not found states
  if (isBlocked) {
    return <ProfileBlockedState />
  }

  if (isNotFound) {
    return (
      <div className="min-h-full flex items-center justify-center px-4 py-16">
        <EmptyState title="Пользователь не найден" />
      </div>
    )
  }

  // Extract data
  const brightestHabit = habits ? getBrightestHabit(habits) : null
  const visibleHabitsCount = habits?.length || 0

  // Convert daily_activity to logs format for ProfileActivity
  const logsFromDailyActivity: HabitLogOutputSchema[] =
    dashboard?.daily_activity.flatMap((point) =>
      Array.from({ length: point.completed_count }, (_, i) => ({
        id: `${point.date}-${i}`,
        habit_id: '',
        completed_date: point.date,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        user_id: userId,
      }))
    ) || []

  const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.04 } },
  } as const

  const item = {
    hidden: { opacity: 0, y: 8 },
    show: { opacity: 1, y: 0 },
  } as const

  return (
    <div className="min-h-full pb-24 lg:pb-8">
      <div className="max-w-5xl mx-auto">
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-12 py-8">
          {/* Hero section */}
          <motion.div variants={item}>
            {isLoading || relationshipPending ? (
              <ProfileHeroSkeleton />
            ) : isError && !isBlocked && !isNotFound ? (
              <ErrorState message="Не удалось загрузить данные профиля" onRetry={refetch} />
            ) : userIdentity && dashboard ? (
              <UserProfileHero
                userId={userId}
                username={userIdentity.username}
                pfpUrl={userIdentity.pfp_url || defaultPfp}
                visibleHabitsCount={visibleHabitsCount}
                bestStreak={dashboard.summary.best_streak_overall}
                totalCompletions={dashboard.summary.total_completions_all_time}
                achievementsCount={dashboard.summary.achievements_unlocked}
                brightestHabit={brightestHabit}
                isFriend={isFriend}
                isIncomingRequest={isIncomingRequest}
                isOutgoingRequest={isOutgoingRequest}
              />
            ) : (
              <EmptyState title="Не удалось загрузить профиль" />
            )}
          </motion.div>

          {/* More sections continue... */}

          {/* Highlights */}
          <motion.div variants={item}>
            {isLoading ? (
              <ProfileHighlightsSkeleton />
            ) : dashboard && !isBlocked ? (
              <ProfileHighlights
                visibleHabits={habits || []}
                weekdayActivity={dashboard.weekday_activity}
                userCreatedAt={new Date().toISOString()}
              />
            ) : null}
          </motion.div>

          {/* Activity heatmap */}
          <motion.div variants={item}>
            {isLoading ? (
              <ProfileActivitySkeleton />
            ) : dashboard && !isBlocked ? (
              <ProfileActivity logs={logsFromDailyActivity} />
            ) : null}
          </motion.div>

          {/* Habits showcase */}
          <motion.div variants={item}>
            {isLoading ? (
              <ProfileHabitsShowcaseSkeleton />
            ) : habits && habits.length > 0 && !isBlocked ? (
              <ProfileHabitsShowcase habits={habits} privateCount={0} />
            ) : null}
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}

export default UserProfilePage
