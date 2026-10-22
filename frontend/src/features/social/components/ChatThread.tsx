import { useEffect, useRef, useMemo } from 'react'
import { ArrowLeft } from 'lucide-react'
import { format, isToday, isYesterday, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { useQueryClient } from '@tanstack/react-query'
import { useGetHistoryApiV1SocialMessagesPeerIdGet } from '@/api/generated/💬-social/💬-social'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { Button } from '@/shared/ui/button'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Skeleton } from '@/shared/ui/skeleton'
import { ErrorState } from '@/shared/components/ErrorState'
import { EmptyState } from '@/shared/components/EmptyState'
import { ChatMessageBubble } from './ChatMessageBubble'
import { ChatComposer } from './ChatComposer'
import { CHAT_HISTORY_PARAMS } from '../lib/constants'
import { isMessagesQuery } from '../lib/query-keys'
import defaultPfp from '@/assets/defaults/default-pfp.webp'
import type { FriendSchema, MessageOutputSchema } from '@/api/generated/model'

type ChatThreadProps = {
  peer: FriendSchema
  onBack?: () => void
  socketRef: React.RefObject<WebSocket | null>
}

export function ChatThread({ peer, onBack, socketRef }: ChatThreadProps) {
  const queryClient = useQueryClient()
  const { data: currentUser } = useGetMeApiV1UsersMeGet()
  const {
    data: messages,
    isLoading,
    isError,
    refetch,
  } = useGetHistoryApiV1SocialMessagesPeerIdGet(peer.id, CHAT_HISTORY_PARAMS)
  const bottomRef = useRef<HTMLDivElement>(null)
  const isInitialLoadRef = useRef(true)
  const markedAsReadRef = useRef<Set<string>>(new Set())

  useEffect(() => {
    if (messages && messages.length > 0) {
      const behavior = isInitialLoadRef.current ? 'auto' : 'smooth'
      bottomRef.current?.scrollIntoView({ behavior })
      if (isInitialLoadRef.current) {
        isInitialLoadRef.current = false
      }
    }
  }, [messages])

  // Mark unread incoming messages as read
  useEffect(() => {
    if (!messages || !currentUser || !socketRef?.current) return

    const unreadIncoming = messages.filter(
      (msg) => 
        msg.receiver_id === currentUser.id && 
        !msg.is_read &&
        !markedAsReadRef.current.has(msg.id)
    )

    if (unreadIncoming.length === 0) return

    const ws = socketRef.current
    if (ws.readyState !== WebSocket.OPEN) return

    const messageIds = unreadIncoming.map((msg) => msg.id)
    
    // Optimistically mark as read in all message caches
    const updateCache = (old: MessageOutputSchema[] | undefined) => {
      if (!old) return old
      return old.map((msg) =>
        messageIds.includes(msg.id)
          ? { ...msg, is_read: true, read_at: new Date().toISOString() }
          : msg
      )
    }
    
    queryClient.setQueriesData<MessageOutputSchema[]>(
      { predicate: (q) => isMessagesQuery(q) && String(q.queryKey[0]).endsWith(`/${peer.id}`) },
      updateCache
    )
    
    // Mark as processed to avoid duplicate requests
    messageIds.forEach(id => markedAsReadRef.current.add(id))
    
    // Send WebSocket event
    ws.send(
      JSON.stringify({
        type: 'mark_read',
        message_ids: messageIds,
      })
    )
  }, [messages, currentUser, socketRef, peer.id, queryClient])
  
  // Reset marked set when peer changes
  useEffect(() => {
    markedAsReadRef.current.clear()
  }, [peer.id])

  const groupedMessages = useMemo(() => {
    if (!messages) return []

    const sortedMessages = [...messages].sort(
      (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    )

    const groups: Array<{
      date: string
      label: string
      items: typeof messages
    }> = []
    let currentDate: string | null = null

    sortedMessages.forEach((msg) => {
      const msgDate = parseISO(msg.created_at)
      const dateKey = format(msgDate, 'yyyy-MM-dd')

      if (dateKey !== currentDate) {
        let label: string
        if (isToday(msgDate)) label = 'Сегодня'
        else if (isYesterday(msgDate)) label = 'Вчера'
        else label = format(msgDate, 'd MMMM', { locale: ru })

        groups.push({ date: dateKey, label, items: [] })
        currentDate = dateKey
      }

      groups[groups.length - 1].items.push(msg)
    })

    return groups
  }, [messages])

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="h-16 border-b border-border flex items-center gap-3 px-4 shrink-0">
          <Skeleton className="h-10 w-10 rounded-full" />
          <Skeleton className="h-5 w-32" />
        </div>
        <div className="flex-1 p-4 space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className={`flex gap-3 ${i % 2 === 0 ? '' : 'flex-row-reverse'}`}>
              <Skeleton
                className={`h-14 ${i % 2 === 0 ? 'w-48' : 'w-56'} rounded-[16px]`}
              />
            </div>
          ))}
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="h-full flex items-center justify-center">
        <ErrorState message="Не удалось загрузить историю сообщений" onRetry={refetch} />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      <div className="h-16 border-b border-border flex items-center gap-3 px-4 shrink-0 bg-surface">
        {onBack && (
          <Button variant="ghost" size="icon" onClick={onBack} aria-label="Назад">
            <ArrowLeft size={20} />
          </Button>
        )}
        <Avatar className="h-10 w-10">
          <AvatarImage
            src={peer.pfp_url}
            alt={peer.username}
            onError={(e) => {
              e.currentTarget.src = defaultPfp
            }}
          />
          <AvatarFallback>
            <img src={defaultPfp} alt={peer.username} />
          </AvatarFallback>
        </Avatar>
        <h2 className="text-[15px] font-medium text-foreground">{peer.username}</h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6 min-h-0">
        {!messages || messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <EmptyState title="Сообщений пока нет" description="Напишите первым!" />
          </div>
        ) : (
          groupedMessages.map((group) => (
            <div key={group.date}>
              <div className="flex justify-center mb-4">
                <span className="text-xs text-muted-foreground bg-surface-muted px-3 py-1 rounded-full">
                  {group.label}
                </span>
              </div>
              <div className="space-y-3">
                {group.items.map((msg) => (
                  <ChatMessageBubble
                    key={msg.id}
                    message={msg}
                    isOwn={msg.sender_id === currentUser?.id}
                  />
                ))}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <ChatComposer receiverId={peer.id} socketRef={socketRef} />
    </div>
  )
}
