import { Link } from 'react-router-dom'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Progress } from '@/shared/ui/progress'
import { Button } from '@/shared/ui/button'
import { pluralize } from '@/shared/lib/pluralize'
import defaultPfp from '@/assets/defaults/default-pfp.webp'
import type { FriendSchema } from '@/api/generated/model'
import type { FriendActivity } from '../hooks/useFriendsActivity'

type FriendsTodayCardProps = {
  friends: FriendSchema[]
  activityMap: Map<string, FriendActivity>
}

export function FriendsTodayCard({ friends, activityMap }: FriendsTodayCardProps) {
  const activeFriends = friends.filter((f) => activityMap.get(f.id)?.activeToday)
  const activeCount = activeFriends.length
  const totalCount = friends.length

  if (totalCount === 0) return null

  const progress = totalCount > 0 ? (activeCount / totalCount) * 100 : 0
  const displayedFriends = activeFriends.slice(0, 5)
  const remainingCount = activeCount - 5

  return (
    <div className="bg-surface-elevated rounded-2xl p-4 shadow-sm">
      <p className="text-[13px] uppercase text-muted-foreground mb-3 tracking-wide">
        Сегодня у друзей
      </p>

      {activeCount === 0 ? (
        <div className="text-center py-4">
          <p className="text-sm text-muted-foreground mb-3">
            Сегодня пока тихо
          </p>
          <Link to="/feed">
            <Button variant="ghost" size="sm">
              Посмотреть ленту
            </Button>
          </Link>
        </div>
      ) : (
        <>
          <p className="text-sm text-foreground mb-2">
            {activeCount} из {totalCount} {pluralize(totalCount, 'друг', 'друга', 'друзей')}{' '}
            уже {pluralize(activeCount, 'отметился', 'отметились', 'отметились')}
          </p>
          <Progress value={progress} className="h-1.5 mb-3" />
          <div className="flex items-center -space-x-2">
            {displayedFriends.map((friend) => (
              <Avatar
                key={friend.id}
                className="h-8 w-8 border-2 border-surface-elevated"
              >
                <AvatarImage src={friend.pfp_url} alt={friend.username} />
                <AvatarFallback>
                  <img src={defaultPfp} alt="" />
                </AvatarFallback>
              </Avatar>
            ))}
            {remainingCount > 0 && (
              <div className="h-8 w-8 rounded-full bg-muted border-2 border-surface-elevated flex items-center justify-center">
                <span className="text-xs font-medium text-muted-foreground">
                  +{remainingCount}
                </span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
