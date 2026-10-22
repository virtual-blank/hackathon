import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MessageCircle, UserPlus, Check, X } from 'lucide-react'
import { toast } from 'sonner'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { pluralizeDays } from '@/shared/lib/date'
import { pluralize } from '@/shared/lib/pluralize'
import { useFriendActions } from '@/features/friends/hooks/useFriendActions'
import type { HabitOutputSchema } from '@/api/generated/model'
import defaultPfp from '@/assets/defaults/default-pfp.webp'
import { RelationStatus } from '@/api/generated/model'

type UserProfileHeroProps = {
  userId: string
  username: string
  pfpUrl: string
  visibleHabitsCount: number
  bestStreak: number
  totalCompletions: number
  achievementsCount: number
  brightestHabit: HabitOutputSchema | null
  isFriend: boolean
  isIncomingRequest: boolean
  isOutgoingRequest: boolean
}

export function UserProfileHero({
  userId,
  username,
  pfpUrl,
  visibleHabitsCount,
  bestStreak,
  totalCompletions,
  achievementsCount,
  brightestHabit,
  isFriend,
  isIncomingRequest,
  isOutgoingRequest,
}: UserProfileHeroProps) {
  const navigate = useNavigate()
  const { sendRequest, acceptRequest, declineRequest } = useFriendActions()
  const [localRequestSent, setLocalRequestSent] = useState(false)
  const [localAccepted, setLocalAccepted] = useState(false)

  const habitColor = brightestHabit?.color_hex || null

  const handleMessage = () => {
    navigate(`/chat?peer=${userId}`, {
      state: { id: userId, username, pfp_url: pfpUrl }
    })
  }

  const handleAddFriend = () => {
    sendRequest.mutate(
      { targetId: userId },
      {
        onSuccess: (data) => {
          if (data.status === RelationStatus.accepted) {
            setLocalAccepted(true)
            toast.success('Вы теперь друзья')
          } else if (data.status === RelationStatus.pending) {
            setLocalRequestSent(true)
            toast.success('Заявка отправлена')
          } else if (data.status === RelationStatus.blocked) {
            toast.error('Не удалось отправить заявку')
          }
        },
        onError: () => {
          toast.error('Не удалось отправить заявку')
        },
      }
    )
  }

  const handleAccept = () => {
    acceptRequest.mutate({ senderId: userId }, { onSuccess: () => setLocalAccepted(true) })
  }

  const handleDecline = () => {
    declineRequest.mutate({ senderId: userId })
  }

  const showFriendBadge = isFriend || localAccepted
  const showRequestSent = (isOutgoingRequest || localRequestSent) && !showFriendBadge
  const showAddFriend = !isFriend && !isIncomingRequest && !isOutgoingRequest && !localRequestSent && !localAccepted

  return (
    <div className="relative">
      {habitColor && (
        <div
          className="absolute inset-0 rounded-[24px] pointer-events-none opacity-[0.08] blur-[64px]"
          style={{
            background: `radial-gradient(circle at 50% 30%, ${habitColor}, transparent 60%)`,
          }}
        />
      )}

      <div className="relative px-4 py-8 space-y-6">
        <div className="flex flex-col items-center gap-3">
          <Avatar className="w-24 h-24 lg:w-[120px] lg:h-[120px] ring-2 ring-border">
            <AvatarImage src={pfpUrl || defaultPfp} alt={username} />
            <AvatarFallback>
              <img src={defaultPfp} alt="" className="w-full h-full object-cover" />
            </AvatarFallback>
          </Avatar>
          <div className="text-center space-y-2">
            <h1 className="font-display text-3xl lg:text-4xl font-semibold">{username}</h1>
            {showFriendBadge && (
              <Badge variant="secondary" className="text-xs">
                В друзьях
              </Badge>
            )}
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3">
          <Button onClick={handleMessage} className="min-w-[140px]">
            <MessageCircle className="h-4 w-4 mr-1.5" strokeWidth={1.75} />
            Написать
          </Button>

          {showAddFriend && (
            <Button onClick={handleAddFriend} variant="secondary" disabled={sendRequest.isPending} className="min-w-[140px]">
              <UserPlus className="h-4 w-4 mr-1.5" strokeWidth={1.75} />
              Добавить в друзья
            </Button>
          )}

          {showRequestSent && (
            <Button variant="secondary" disabled className="min-w-[140px]">
              Заявка отправлена
            </Button>
          )}

          {isIncomingRequest && !localAccepted && (
            <>
              <Button onClick={handleAccept} disabled={acceptRequest.isPending} className="min-w-[120px]">
                <Check className="h-4 w-4 mr-1.5" strokeWidth={1.75} />
                Принять
              </Button>
              <Button onClick={handleDecline} variant="destructive" disabled={declineRequest.isPending} className="min-w-[120px]">
                <X className="h-4 w-4 mr-1.5" strokeWidth={1.75} />
                Отклонить
              </Button>
            </>
          )}
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 max-w-2xl mx-auto">
          <div className="text-center space-y-1">
            <div className="font-display text-3xl font-semibold tabular-nums">{visibleHabitsCount}</div>
            <div className="text-xs text-muted-foreground">{pluralize(visibleHabitsCount, 'Привычка', 'Привычки', 'Привычек')}</div>
          </div>
          <div className="text-center space-y-1">
            <div className="font-display text-3xl font-semibold tabular-nums">
              {bestStreak} {pluralizeDays(bestStreak)}
            </div>
            <div className="text-xs text-muted-foreground">Лучшая серия</div>
          </div>
          <div className="text-center space-y-1">
            <div className="font-display text-3xl font-semibold tabular-nums">{totalCompletions}</div>
            <div className="text-xs text-muted-foreground">{pluralize(totalCompletions, 'Отметка', 'Отметки', 'Отметок')}</div>
          </div>
          <div className="text-center space-y-1">
            <div className="font-display text-3xl font-semibold tabular-nums">{achievementsCount}</div>
            <div className="text-xs text-muted-foreground">{pluralize(achievementsCount, 'Достижение', 'Достижения', 'Достижений')}</div>
          </div>
        </div>
      </div>
    </div>
  )
}
