import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { pluralize } from '@/shared/lib/pluralize'
import defaultPfp from '@/assets/defaults/default-pfp.webp'
import { UserLink } from '@/shared/components/UserLink'
import type { FriendSchema } from '@/api/generated/model'
import type { FriendActivity } from '../hooks/useFriendsActivity'

type LeadersCardProps = {
  friends: FriendSchema[]
  activityMap: Map<string, FriendActivity>
}

export function LeadersCard({ friends, activityMap }: LeadersCardProps) {
  // Sort friends by totalLogs, take top 3
  const leaders = [...friends]
    .map((friend) => ({
      friend,
      totalLogs: activityMap.get(friend.id)?.totalLogs || 0,
    }))
    .filter((item) => item.totalLogs > 0)
    .sort((a, b) => b.totalLogs - a.totalLogs)
    .slice(0, 3)

  if (leaders.length === 0) return null

  return (
    <div className="bg-surface-elevated rounded-2xl p-4 shadow-sm">
      <p className="text-[13px] uppercase text-muted-foreground mb-3 tracking-wide">
        Лидеры по выполнениям
      </p>

      <div className="space-y-3">
        {leaders.map((item, index) => (
          <div key={item.friend.id} className="flex items-center gap-3">
            <span className="text-lg font-display font-semibold text-muted-foreground w-6 shrink-0">
              {index + 1}
            </span>
            <UserLink
              userId={item.friend.id}
              username={item.friend.username}
              pfpUrl={item.friend.pfp_url}
              className="flex items-center gap-3 flex-1 min-w-0"
            >
              <Avatar className="h-8 w-8 shrink-0">
                <AvatarImage
                  src={item.friend.pfp_url}
                  alt={item.friend.username}
                />
                <AvatarFallback>
                  <img src={defaultPfp} alt="" />
                </AvatarFallback>
              </Avatar>
              <p className="flex-1 min-w-0 text-[15px] font-medium text-foreground truncate hover:underline">
                {item.friend.username}
              </p>
            </UserLink>
            <p className="text-[13px] text-muted-foreground shrink-0">
              {item.totalLogs}{' '}
              {pluralize(item.totalLogs, 'выполнение', 'выполнения', 'выполнений')}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
