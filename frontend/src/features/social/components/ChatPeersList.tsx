import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Users } from 'lucide-react'
import { useGetFriendsApiV1FriendsGet } from '@/api/generated/🤝-friends/🤝-friends'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { Input } from '@/shared/ui/input'
import { Skeleton } from '@/shared/ui/skeleton'
import { ErrorState } from '@/shared/components/ErrorState'
import { EmptyState } from '@/shared/components/EmptyState'
import { useChatPeers } from '../hooks/useChatPeers'
import { ChatPeerRow } from './ChatPeerRow'

type ChatPeersListProps = {
  selectedPeerId?: string
  onSelectPeer: (peerId: string) => void
}

export function ChatPeersList({ selectedPeerId, onSelectPeer }: ChatPeersListProps) {
  const navigate = useNavigate()
  const { data: currentUser } = useGetMeApiV1UsersMeGet()
  const {
    data: friends,
    isLoading,
    isError,
    refetch,
  } = useGetFriendsApiV1FriendsGet({ limit: 100, offset: 0 })
  const [search, setSearch] = useState('')

  const peers = useChatPeers(friends)

  const filteredPeers = useMemo(() => {
    if (!search.trim()) return peers
    const query = search.trim().toLowerCase()
    return peers.filter((p) => p.friend.username.toLowerCase().includes(query))
  }, [peers, search])

  if (isLoading) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-border">
          <h1 className="font-display text-2xl font-medium text-foreground mb-3">Чат</h1>
          <Skeleton className="h-11 w-full" />
        </div>
        <div className="flex-1 p-2 space-y-2 overflow-y-auto min-h-0">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3 p-3">
              <Skeleton className="h-12 w-12 rounded-full" />
              <div className="flex-1 space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-3 w-full" />
              </div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="h-full flex items-center justify-center p-4">
        <ErrorState message="Не удалось загрузить список друзей" onRetry={refetch} />
      </div>
    )
  }

  if (!friends || friends.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-4">
        <EmptyState
          title="У вас пока нет друзей для общения"
          description="Добавьте друзей, чтобы начать переписку"
          illustration={
            <Users className="w-12 h-12 text-muted-foreground" strokeWidth={1.75} />
          }
          actionLabel="Найти друзей"
          onAction={() => navigate('/friends')}
        />
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border shrink-0">
        <h1 className="font-display text-2xl font-medium text-foreground mb-3">Чат</h1>
        <div className="relative">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
            size={18}
          />
          <Input
            type="text"
            placeholder="Поиск..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 bg-surface-muted"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-2 min-h-0">
        {filteredPeers.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-sm text-muted-foreground">Ничего не найдено</p>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredPeers.map((peer) => (
              <ChatPeerRow
                key={peer.friend.id}
                peer={peer}
                currentUserId={currentUser?.id}
                isActive={peer.friend.id === selectedPeerId}
                onSelect={() => onSelectPeer(peer.friend.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

