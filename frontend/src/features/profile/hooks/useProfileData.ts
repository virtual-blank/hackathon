import { useGetMeApiV1UsersMeGet } from "@/api/generated/👤-users/👤-users";
import { useGetFriendsApiV1FriendsGet } from "@/api/generated/🤝-friends/🤝-friends";
import { useGetHabitsApiV1HabitsGet } from "@/api/generated/🏃-habits/🏃-habits";
import { useGetDashboardApiV1AnalyticsDashboardGet } from "@/api/generated/📊-analytics/📊-analytics";
import { useGetLogsInRangeApiV1HabitsLogsGet } from "@/api/generated/🏃-habits/🏃-habits";
import { format, subDays } from "date-fns";

export function useProfileData() {
  const userQuery = useGetMeApiV1UsersMeGet();
  const friendsQuery = useGetFriendsApiV1FriendsGet({ limit: 100 });
  const habitsQuery = useGetHabitsApiV1HabitsGet({ limit: 100 });
  const dashboardQuery = useGetDashboardApiV1AnalyticsDashboardGet({ activity_days: 30 });

  // Logs for activity heatmap (~26 weeks = 182 days)
  const dateFrom = format(subDays(new Date(), 181), "yyyy-MM-dd");
  const dateTo = format(new Date(), "yyyy-MM-dd");
  const logsQuery = useGetLogsInRangeApiV1HabitsLogsGet({ date_from: dateFrom, date_to: dateTo });

  return {
    user: userQuery.data,
    isUserLoading: userQuery.isLoading,
    isUserError: userQuery.isError,
    refetchUser: userQuery.refetch,

    friends: friendsQuery.data,
    isFriendsLoading: friendsQuery.isLoading,
    isFriendsError: friendsQuery.isError,
    refetchFriends: friendsQuery.refetch,

    habits: habitsQuery.data,
    isHabitsLoading: habitsQuery.isLoading,
    isHabitsError: habitsQuery.isError,
    refetchHabits: habitsQuery.refetch,

    dashboard: dashboardQuery.data,
    isDashboardLoading: dashboardQuery.isLoading,
    isDashboardError: dashboardQuery.isError,
    refetchDashboard: dashboardQuery.refetch,

    logs: logsQuery.data,
    isLogsLoading: logsQuery.isLoading,
    isLogsError: logsQuery.isError,
    refetchLogs: logsQuery.refetch,
  };
}
