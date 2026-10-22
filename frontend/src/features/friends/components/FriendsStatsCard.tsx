import { useGetDashboardApiV1AnalyticsDashboardGet } from '@/api/generated/📊-analytics/📊-analytics'
import { pluralize } from '@/shared/lib/pluralize'
import type { FriendSchema } from '@/api/generated/model'

type FriendsStatsCardProps = {
  friends: FriendSchema[]
}

export function FriendsStatsCard({ friends }: FriendsStatsCardProps) {
  const { data: dashboardData, isError } =
    useGetDashboardApiV1AnalyticsDashboardGet()

  if (isError || !dashboardData) return null

  const totalPushes = dashboardData.summary.total_pushes_received
  const totalShames = dashboardData.summary.total_shames_received

  return (
    <div className="bg-surface-elevated rounded-2xl p-4 shadow-sm">
      <p className="text-[13px] uppercase text-muted-foreground mb-4 tracking-wide">
        Ваша поддержка
      </p>

      <div className="grid grid-cols-3 gap-3">
        <div>
          <p className="text-2xl font-display font-semibold text-foreground tabular-nums">
            {friends.length}
          </p>
          <p className="text-[12px] text-muted-foreground mt-1">
            {pluralize(friends.length, 'Друг', 'Друга', 'Друзей')}
          </p>
        </div>

        <div>
          <p className="text-2xl font-display font-semibold text-foreground tabular-nums">
            {totalPushes}
          </p>
          <p className="text-[12px] text-muted-foreground mt-1">
            {pluralize(totalPushes, 'Пуш', 'Пуша', 'Пушей')} получено
          </p>
        </div>

        <div>
          <p className="text-2xl font-display font-semibold text-foreground tabular-nums">
            {totalShames}
          </p>
          <p className="text-[12px] text-muted-foreground mt-1">
            {pluralize(totalShames, 'Шейм', 'Шейма', 'Шеймов')} получено
          </p>
        </div>
      </div>
    </div>
  )
}
