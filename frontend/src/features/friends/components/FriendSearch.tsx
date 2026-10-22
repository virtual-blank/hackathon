import { useState, useRef, forwardRef } from 'react'
import { Link } from 'react-router-dom'
import { Search, X, UserPlus, Check } from 'lucide-react'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { Input } from '@/shared/ui/input'
import { EmptyState } from '@/shared/components/EmptyState'
import { Skeleton } from '@/shared/ui/skeleton'
import { useDebouncedValue } from '@/shared/lib/use-debounced-value'
import { useSearchUsersApiV1UsersSearchGet } from '@/api/generated/👤-users/👤-users'
import { useFriendActions } from '../hooks/useFriendActions'
import { toast } from 'sonner'
import defaultPfp from '@/assets/defaults/default-pfp.webp'
import type { FriendSchema } from '@/api/generated/model'

type FriendSearchProps = {
  currentUserId: string
  friends: FriendSchema[]
  incoming: FriendSchema[]
  outgoing: FriendSchema[]
}

export const FriendSearch = forwardRef<HTMLInputElement, FriendSearchProps>(function FriendSearch({
  currentUserId,
  friends,
  incoming,
  outgoing,
}, ref) {
  const [searchValue, setSearchValue] = useState('')
  const internalRef = useRef<HTMLInputElement>(null)
  const inputRef = (ref as React.RefObject<HTMLInputElement>) || internalRef
  const debouncedValue = useDebouncedValue(searchValue, 300)

  const { sendRequest } = useFriendActions()

  const { data: searchResults, isLoading } = useSearchUsersApiV1UsersSearchGet(
    { username: debouncedValue, limit: 20 },
    {
      query: {
        enabled: debouncedValue.length >= 2,
      },
    }
  )

  const filteredResults = searchResults?.filter(
    (user) => user.id !== currentUserId
  )

  const getRelation = (userId: string) => {
    if (friends.some((f) => f.id === userId)) return 'friend'
    if (incoming.some((r) => r.id === userId)) return 'incoming'
    if (outgoing.some((r) => r.id === userId)) return 'outgoing'
    return 'none'
  }

  const handleSendRequest = (targetId: string) => {
    sendRequest.mutate(
      { targetId },
      {
        onSuccess: (data) => {
          if (data.status === 'accepted') {
            toast.success('Вы теперь друзья')
          } else if (data.status === 'pending') {
            toast.success('Заявка отправлена')
          }
        },
        onError: () => {
          toast.error(`Не удалось отправить заявку этому пользователю`)
        },
      }
    )
  }

  const handleClear = () => {
    setSearchValue('')
    inputRef.current?.focus()
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search
          className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
          strokeWidth={1.75}
        />
        <Input
          ref={inputRef}
          type="text"
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
          placeholder="Найти по username"
          maxLength={16}
          className="h-11 rounded-full pl-11 pr-11"
        />
        {searchValue && (
          <button
            onClick={handleClear}
            aria-label="Очистить"
            className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" strokeWidth={1.75} />
          </button>
        )}
      </div>

      {debouncedValue.length >= 2 && (
        <div className="space-y-1">
          <p className="text-sm font-medium text-muted-foreground px-1 mb-2">
            Результаты поиска
          </p>

          {isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-14 flex items-center gap-3 px-3">
                  <Skeleton className="h-10 w-10 rounded-full" />
                  <Skeleton className="h-4 flex-1" />
                  <Skeleton className="h-9 w-24" />
                </div>
              ))}
            </div>
          ) : !filteredResults || filteredResults.length === 0 ? (
            <EmptyState title="Никого не нашли" />
          ) : (
            filteredResults.map((user) => {
              const relation = getRelation(user.id)
              return (
                <div
                  key={user.id}
                  className="h-14 flex items-center gap-3 px-3 -mx-3 rounded-2xl transition-colors hover:bg-muted/60"
                >
                  <Link to={`/users/${user.id}`} state={{ id: user.id, username: user.username, pfp_url: user.pfp_url }} className="flex items-center gap-3 flex-1 min-w-0">
                    <Avatar className="h-10 w-10 shrink-0">
                      <AvatarImage src={user.pfp_url} alt={user.username} />
                      <AvatarFallback>
                        <img src={defaultPfp} alt="" />
                      </AvatarFallback>
                    </Avatar>
                    <p className="flex-1 min-w-0 text-[15px] font-medium text-foreground truncate">
                      {user.username}
                    </p>
                  </Link>
                  {relation === 'friend' ? (
                    <Badge variant="secondary" className="shrink-0">
                      <Check className="h-3 w-3 mr-1" strokeWidth={2} />В друзьях
                    </Badge>
                  ) : relation === 'outgoing' ? (
                    <Button size="sm" variant="secondary" disabled className="h-9">
                      Заявка отправлена
                    </Button>
                  ) : relation === 'incoming' ? (
                    <Button
                      size="sm"
                      className="h-9"
                      onClick={() => {
                        /* Accept handled in RequestRow */
                      }}
                    >
                      Принять
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      className="h-9"
                      onClick={() => handleSendRequest(user.id)}
                      disabled={sendRequest.isPending}
                    >
                      <UserPlus className="h-4 w-4 mr-1.5" strokeWidth={1.75} />
                      Добавить
                    </Button>
                  )}
                </div>
              )
            })
          )}
        </div>
      )}
    </div>
  )
})
