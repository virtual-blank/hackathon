import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/shared/ui/button'
import { EmptyState } from '@/shared/components/EmptyState'
import { Users } from 'lucide-react'
import { FriendRow } from './FriendRow'
import type { FriendSchema } from '@/api/generated/model'
import type { FriendActivity } from '../hooks/useFriendsActivity'

type FriendsListProps = {
  friends: FriendSchema[]
  activityMap: Map<string, FriendActivity>
  onFocusSearch: () => void
}

export function FriendsList({
  friends,
  activityMap,
  onFocusSearch,
}: FriendsListProps) {
  const navigate = useNavigate()
  const [limit, setLimit] = useState(50)

  const displayedFriends = friends.slice(0, limit)
  const hasMore = friends.length > limit

  if (friends.length === 0) {
    return (
      <EmptyState
        title="Пока никого"
        description="Начните искать друзей, чтобы добавить их в список"
        actionLabel="Найти друзей"
        onAction={onFocusSearch}
        illustration={<Users className="w-16 h-16 text-muted-foreground" strokeWidth={1.75} />}
      />
    )
  }

  return (
    <div className="space-y-1">
      {displayedFriends.map((friend) => (
        <FriendRow
          key={friend.id}
          friend={friend}
          activity={activityMap.get(friend.id) || null}
          onNavigateChat={() => navigate(`/chat?peer=${friend.id}`)}
        />
      ))}

      {hasMore && (
        <div className="pt-2 flex justify-center">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setLimit((prev) => prev + 50)}
          >
            Показать ещё
          </Button>
        </div>
      )}
    </div>
  )
}
