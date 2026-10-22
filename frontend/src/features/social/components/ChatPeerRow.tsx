import { format, isToday, isYesterday, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Check, CheckCheck } from 'lucide-react'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/lib/utils'
import defaultPfp from '@/assets/defaults/default-pfp.webp'
import type { ChatPeerWithPreview } from '../hooks/useChatPeers'

type ChatPeerRowProps = {
  peer: ChatPeerWithPreview
  currentUserId: string | undefined
  isActive: boolean
  onSelect: () => void
}

export function ChatPeerRow({ peer, currentUserId, isActive, onSelect }: ChatPeerRowProps) {
  const { friend, lastMessage, isLoading } = peer

  let timeLabel = ''
  if (lastMessage) {
    const msgDate = parseISO(lastMessage.created_at)
    if (isToday(msgDate)) {
      timeLabel = format(msgDate, 'HH:mm', { locale: ru })
    } else if (isYesterday(msgDate)) {
      timeLabel = 'Вчера'
    } else {
      timeLabel = format(msgDate, 'd MMM', { locale: ru })
    }
  }

  const isMyMessage = lastMessage && lastMessage.sender_id === currentUserId
  const isUnread = lastMessage && !isMyMessage && lastMessage.is_read === false

  let previewText = 'Нет сообщений'
  if (lastMessage) {
    previewText = isMyMessage ? `Вы: ${lastMessage.content}` : lastMessage.content
  }

  return (
    <button
      onClick={onSelect}
      className={cn(
        'w-full flex items-start gap-3 p-3 rounded-xl transition-colors relative min-h-[56px]',
        isActive
          ? 'bg-surface-elevated text-foreground shadow-[0_1px_2px_rgba(20,20,30,0.04)] before:absolute before:left-0 before:top-1/2 before:-translate-y-1/2 before:w-[3px] before:h-8 before:bg-primary before:rounded-r-full'
          : 'hover:bg-surface-muted/50'
      )}
      aria-label={`Чат с ${friend.username}`}
      aria-current={isActive ? 'page' : undefined}
    >
      <Avatar className="h-12 w-12 shrink-0">
        <AvatarImage
          src={friend.pfp_url}
          alt={friend.username}
          onError={(e) => {
            e.currentTarget.src = defaultPfp
          }}
        />
        <AvatarFallback>
          <img src={defaultPfp} alt={friend.username} />
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 min-w-0 text-left">
        <div className="flex items-baseline justify-between gap-2 mb-1">
          <p className="text-[15px] font-medium text-foreground truncate">
            {friend.username}
          </p>
          {isLoading ? (
            <Skeleton className="h-3 w-12 shrink-0" />
          ) : (
            lastMessage && (
              <span className="text-xs text-muted-foreground tabular-nums shrink-0">
                {timeLabel}
              </span>
            )
          )}
        </div>

        <div className="flex items-center justify-between gap-2">
          {isLoading ? (
            <Skeleton className="h-4 flex-1" />
          ) : (
            <p
              className={cn(
                'text-sm truncate flex-1',
                isUnread ? 'font-medium text-foreground' : 'text-muted-foreground'
              )}
            >
              {previewText}
            </p>
          )}

          {!isLoading && lastMessage && (
            <div className="shrink-0 flex items-center">
              {isMyMessage ? (
                <span className="text-muted-foreground">
                  {lastMessage.is_read ? <CheckCheck size={14} /> : <Check size={14} />}
                </span>
              ) : (
                isUnread && (
                  <div className="h-2 w-2 rounded-full bg-primary" aria-label="Непрочитано" />
                )
              )}
            </div>
          )}
        </div>
      </div>
    </button>
  )
}
