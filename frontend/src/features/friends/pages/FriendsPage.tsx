import { useRef } from 'react'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import {
  useGetFriendsApiV1FriendsGet,
  useGetRequestsApiV1FriendsRequestsGet,
} from '@/api/generated/🤝-friends/🤝-friends'
import { useFriendsActivity } from '../hooks/useFriendsActivity'
import { useMediaQuery } from '@/shared/hooks/use-media-query'
import { pluralize } from '@/shared/lib/pluralize'
import { FriendsListSkeleton } from '../components/FriendsListSkeleton'
import { FriendsList } from '../components/FriendsList'
import { FriendSearch } from '../components/FriendSearch'
import { RequestsCollapsible } from '../components/RequestsCollapsible'
import { FriendsTodayCard } from '../components/FriendsTodayCard'
import { LeadersCard } from '../components/LeadersCard'
import { FriendsStatsCard } from '../components/FriendsStatsCard'
import { ErrorState } from '@/shared/components/ErrorState'

export function FriendsPage() {
  const isDesktop = useMediaQuery('(min-width: 1280px)')
  const searchInputRef = useRef<HTMLInputElement>(null)

  const { data: me } = useGetMeApiV1UsersMeGet()
  const {
    data: friends,
    isLoading: friendsLoading,
    isError: friendsError,
    refetch: refetchFriends,
  } = useGetFriendsApiV1FriendsGet({ limit: 100, offset: 0 })

  const {
    data: requests,
    isLoading: requestsLoading,
  } = useGetRequestsApiV1FriendsRequestsGet({ limit: 100 })

  const { activityMap } = useFriendsActivity()

  const incoming = requests?.incoming || []
  const outgoing = requests?.outgoing || []

  const handleFocusSearch = () => {
    searchInputRef.current?.focus()
  }

  // Loading / Error states
  if (friendsLoading || requestsLoading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="w-full max-w-5xl px-4">
          <FriendsListSkeleton />
        </div>
      </div>
    )
  }

  if (friendsError) {
    return (
      <div className="h-full flex items-center justify-center">
        <ErrorState
          title="Не удалось загрузить друзей"
          message="Попробуйте обновить страницу"
          onRetry={refetchFriends}
        />
      </div>
    )
  }

  // Desktop layout
  if (isDesktop) {
    return (
      <div className="h-full p-3 overflow-hidden">
        <div className="h-full rounded-[24px] bg-surface border border-border shadow-sm overflow-hidden flex min-h-full flex-col xl:h-full xl:min-h-0 xl:flex-row">
          {/* Left column */}
          <section className="min-w-0 flex-1 overflow-x-hidden px-4 pb-8 pt-8 xl:overflow-y-auto xl:px-8 flex flex-col">
            <div className="mb-6">
              <h1 className="font-display text-[32px] font-semibold text-foreground inline-block">
                Друзья
              </h1>
              <span className="text-[15px] text-muted-foreground ml-3">
                {friends?.length || 0}{' '}
                {pluralize(friends?.length || 0, 'друг', 'друга', 'друзей')}
              </span>
            </div>

            <div className="mb-4">
              <FriendSearch
                ref={searchInputRef}
                currentUserId={me?.id || ''}
                friends={friends || []}
                incoming={incoming}
                outgoing={outgoing}
              />
            </div>

            <div className="flex-1 min-h-0">
              <FriendsList
                friends={friends || []}
                activityMap={activityMap}
                onFocusSearch={handleFocusSearch}
              />
            </div>
          </section>

          {/* Right column */}
          <aside className="shrink-0 overflow-x-hidden xl:w-[380px] 2xl:w-[440px] xl:overflow-y-auto bg-surface-muted border-l border-border flex flex-col px-4 pt-6 pb-8 gap-6 relative">
            <RequestsCollapsible incoming={incoming} outgoing={outgoing} />
            <FriendsTodayCard friends={friends || []} activityMap={activityMap} />
            <LeadersCard friends={friends || []} activityMap={activityMap} />
            <FriendsStatsCard friends={friends || []} />

            {/* Fade gradient at bottom */}
            <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-surface-muted to-transparent pointer-events-none" />
          </aside>
        </div>
      </div>
    )
  }

  // Mobile layout
  return (
    <div className="h-full overflow-y-auto px-4 pt-6 pb-24">
      <div className="mb-6">
        <h1 className="font-display text-[28px] font-semibold text-foreground">
          Друзья
        </h1>
        <span className="text-[15px] text-muted-foreground">
          {friends?.length || 0}{' '}
          {pluralize(friends?.length || 0, 'друг', 'друга', 'друзей')}
        </span>
      </div>

      <div className="mb-4">
        <FriendSearch
          ref={searchInputRef}
          currentUserId={me?.id || ''}
          friends={friends || []}
          incoming={incoming}
          outgoing={outgoing}
        />
      </div>

      <div className="mb-4">
        <RequestsCollapsible incoming={incoming} outgoing={outgoing} />
      </div>

      <div className="mb-6">
        <FriendsList
          friends={friends || []}
          activityMap={activityMap}
          onFocusSearch={handleFocusSearch}
        />
      </div>

      {/* Mobile bottom cards */}
      <div className="space-y-4">
        <FriendsTodayCard friends={friends || []} activityMap={activityMap} />
        <LeadersCard friends={friends || []} activityMap={activityMap} />
        <FriendsStatsCard friends={friends || []} />
      </div>
    </div>
  )
}

