import { useSearchParams, useLocation } from 'react-router-dom'
import { MessageCircle } from 'lucide-react'
import { useGetFriendsApiV1FriendsGet } from '@/api/generated/🤝-friends/🤝-friends'
import { useMediaQuery } from '@/shared/hooks/use-media-query'
import { ChatPeersList } from '../components/ChatPeersList'
import { ChatThread } from '../components/ChatThread'
import { EmptyState } from '@/shared/components/EmptyState'
import { useChatSocketRef } from '../hooks/ChatSocketProvider'

export function ChatPage() {
  const socketRef = useChatSocketRef()
  const location = useLocation()

  const [searchParams, setSearchParams] = useSearchParams()
  const peerIdFromUrl = searchParams.get('peer')
  const isDesktop = useMediaQuery('(min-width: 1024px)')

  const { data: friends } = useGetFriendsApiV1FriendsGet({ limit: 100, offset: 0 })
  
  // Try to get peer from friends list, or from location.state if not a friend
  const stateIdentity = location.state as { id?: string; username?: string; pfp_url?: string } | null
  const selectedPeer = 
    friends?.find((f) => f.id === peerIdFromUrl) ||
    (stateIdentity?.id === peerIdFromUrl && stateIdentity.username && stateIdentity.pfp_url
      ? { id: stateIdentity.id, username: stateIdentity.username, pfp_url: stateIdentity.pfp_url }
      : undefined)

  const handleSelectPeer = (peerId: string) => {
    setSearchParams({ peer: peerId })
  }

  const handleBackToList = () => {
    setSearchParams({})
  }

  if (isDesktop) {
    return (
      <div className="h-full flex overflow-hidden">
        <div className="w-80 shrink-0 border-r border-border bg-surface-muted/40 flex flex-col">
          <ChatPeersList
            selectedPeerId={selectedPeer?.id}
            onSelectPeer={handleSelectPeer}
          />
        </div>

        <div className="flex-1 flex flex-col min-w-0 bg-surface">
          {!selectedPeer ? (
            <div className="h-full flex items-center justify-center">
              <EmptyState
                title="Выберите собеседника"
                description="Выберите друга из списка слева, чтобы начать переписку"
                illustration={
                  <MessageCircle
                    className="w-16 h-16 text-muted-foreground"
                    strokeWidth={1.75}
                  />
                }
              />
            </div>
          ) : (
            <ChatThread peer={selectedPeer} socketRef={socketRef} />
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex overflow-hidden">
      <div className="flex-1 flex flex-col min-w-0">
        {!selectedPeer ? (
          <ChatPeersList selectedPeerId={undefined} onSelectPeer={handleSelectPeer} />
        ) : (
          <ChatThread peer={selectedPeer} onBack={handleBackToList} socketRef={socketRef} />
        )}
      </div>
    </div>
  )
}

