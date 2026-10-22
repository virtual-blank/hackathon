import { useState } from "react";
import { motion } from "motion/react";
import { useProfileData } from "../hooks/useProfileData";
import { useVisibleHabits } from "../hooks/useVisibleHabits";
import { getBrightestHabit, countPrivateHabits, type AudienceType } from "../lib/profile-helpers";
import { ErrorState } from "@/shared/components/ErrorState";
import { ProfileHero } from "../components/ProfileHero";
import { ProfileHeroSkeleton } from "../components/ProfileHeroSkeleton";
import { ProfileHighlights } from "../components/ProfileHighlights";
import { ProfileHighlightsSkeleton } from "../components/ProfileHighlightsSkeleton";
import { ProfileActivity } from "../components/ProfileActivity";
import { ProfileActivitySkeleton } from "../components/ProfileActivitySkeleton";
import { ProfileHabitsShowcase } from "../components/ProfileHabitsShowcase";
import { ProfileHabitsShowcaseSkeleton } from "../components/ProfileHabitsShowcaseSkeleton";
import { ProfileAchievements } from "../components/ProfileAchievements";
import { ProfileAchievementsSkeleton } from "../components/ProfileAchievementsSkeleton";
import { ProfileFriends } from "../components/ProfileFriends";
import { ProfileFriendsSkeleton } from "../components/ProfileFriendsSkeleton";
import { ProfileSupport } from "../components/ProfileSupport";

export function ProfilePage() {
  const [audience, setAudience] = useState<AudienceType>("friends");

  const {
    user,
    isUserLoading,
    isUserError,
    refetchUser,
    friends,
    isFriendsLoading,
    isFriendsError,
    refetchFriends,
    habits,
    isHabitsLoading,
    isHabitsError,
    refetchHabits,
    dashboard,
    isDashboardLoading,
    isDashboardError,
    refetchDashboard,
    logs,
    isLogsLoading,
    isLogsError,
    refetchLogs,
  } = useProfileData();

  const visibleHabits = useVisibleHabits({ habits, audience });
  const privateCount = habits ? countPrivateHabits(habits) : 0;
  const brightestHabit = habits ? getBrightestHabit(visibleHabits) : null;

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
          <motion.div variants={item}>
            {isUserLoading || isDashboardLoading || isFriendsLoading || isHabitsLoading ? (
              <ProfileHeroSkeleton />
            ) : isUserError ? (
              <ErrorState message="Не удалось загрузить данные профиля" onRetry={refetchUser} />
            ) : user && dashboard ? (
              <ProfileHero
                user={user}
                friendsCount={friends?.length || 0}
                visibleHabitsCount={visibleHabits.length}
                bestStreak={dashboard.summary.best_streak_overall}
                totalCompletions={dashboard.summary.total_completions_all_time}
                brightestHabit={brightestHabit}
                audience={audience}
                onAudienceChange={setAudience}
              />
            ) : null}
          </motion.div>

          <motion.div variants={item}>
            {isDashboardLoading || isHabitsLoading ? (
              <ProfileHighlightsSkeleton />
            ) : isDashboardError ? (
              <ErrorState message="Не удалось загрузить хайлайты" onRetry={refetchDashboard} />
            ) : dashboard && user ? (
              <ProfileHighlights
                visibleHabits={visibleHabits}
                weekdayActivity={dashboard.weekday_activity}
                userCreatedAt={user.created_at}
              />
            ) : null}
          </motion.div>

          <motion.div variants={item}>
            {isLogsLoading ? (
              <ProfileActivitySkeleton />
            ) : isLogsError ? (
              <ErrorState message="Не удалось загрузить карту активности" onRetry={refetchLogs} />
            ) : logs ? (
              <ProfileActivity logs={logs} />
            ) : null}
          </motion.div>

          <motion.div variants={item}>
            {isHabitsLoading ? (
              <ProfileHabitsShowcaseSkeleton />
            ) : isHabitsError ? (
              <ErrorState message="Не удалось загрузить привычки" onRetry={refetchHabits} />
            ) : habits ? (
              <ProfileHabitsShowcase habits={visibleHabits} privateCount={privateCount} />
            ) : null}
          </motion.div>

          <motion.div variants={item}>
            {isUserLoading ? (
              <ProfileAchievementsSkeleton />
            ) : isUserError ? (
              <ErrorState message="Не удалось загрузить достижения" onRetry={refetchUser} />
            ) : user ? (
              <ProfileAchievements achievements={user.achievements || []} />
            ) : null}
          </motion.div>

          <motion.div variants={item}>
            {isFriendsLoading ? (
              <ProfileFriendsSkeleton />
            ) : isFriendsError ? (
              <ErrorState message="Не удалось загрузить список друзей" onRetry={refetchFriends} />
            ) : friends ? (
              <ProfileFriends friends={friends} isLimited={friends.length >= 100} />
            ) : null}
          </motion.div>

          <motion.div variants={item}>
            {dashboard && <ProfileSupport totalPushesReceived={dashboard.summary.total_pushes_received} />}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}

export default ProfilePage;
