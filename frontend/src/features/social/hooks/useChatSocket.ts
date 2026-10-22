import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { getAccessToken } from '@/api/mutator'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { getGetHistoryApiV1SocialMessagesPeerIdGetQueryKey } from '@/api/generated/💬-social/💬-social'
import { CHAT_HISTORY_PARAMS, CHAT_PREVIEW_PARAMS, UNREAD_CHECK_PARAMS } from '../lib/constants'
import { isMessagesQuery } from '../lib/query-keys'
import type { MessageOutputSchema } from '@/api/generated/model'

type WSEvent =
  | { type: 'new_message'; message: MessageOutputSchema }
  | { type: 'read'; by: string; message_ids: string[] }
  | { type: 'error'; detail: string }

export function useChatSocket() {
  const queryClient = useQueryClient()
  const { data: currentUser } = useGetMeApiV1UsersMeGet()
  const socketRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<number | undefined>(undefined)
  const reconnectDelayRef = useRef(1000)
  const hasConnectedRef = useRef(false)

  useEffect(() => {
    if (!currentUser) return

    let isMounted = true

    const connect = () => {
      // Защита от двойного подключения
      if (socketRef.current && socketRef.current.readyState <= WebSocket.OPEN) {
        return
      }

      const token = getAccessToken()
      if (!token) {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          if (isMounted) connect()
        }, reconnectDelayRef.current)
        return
      }

      const baseUrl = import.meta.env.VITE_API_URL || ''
      const wsUrl = baseUrl.replace(/^http/, 'ws') + `/api/v1/ws/chat?token=${token}`

      const ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        // Ресинк после обрыва
        if (hasConnectedRef.current) {
          queryClient.invalidateQueries({ predicate: isMessagesQuery })
        }
        socketRef.current = ws
        reconnectDelayRef.current = 1000
        hasConnectedRef.current = true
      }

      ws.onmessage = (event) => {
        try {
          const data: WSEvent = JSON.parse(event.data)

          if (data.type === 'new_message') {
            const msg = data.message
            const peerId = msg.sender_id === currentUser.id ? msg.receiver_id : msg.sender_id
            const isOwnMessage = msg.sender_id === currentUser.id

            const historyKey = getGetHistoryApiV1SocialMessagesPeerIdGetQueryKey(
              peerId,
              CHAT_HISTORY_PARAMS
            )
            
            const existingHistory = queryClient.getQueryData<MessageOutputSchema[]>(historyKey)
            
            if (existingHistory) {
              queryClient.setQueryData<MessageOutputSchema[]>(historyKey, (old) => {
                if (!old) return old
                
                const alreadyExists = old.some((m) => m.id === msg.id)
                if (alreadyExists) {
                  return old
                }

                if (isOwnMessage) {
                  const withoutTemp = old.filter((m) => !m.id.startsWith('temp-'))
                  return [...withoutTemp, msg]
                }

                return [...old, msg]
              })
            } else {
              queryClient.invalidateQueries({ queryKey: historyKey })
            }

            const previewKey = getGetHistoryApiV1SocialMessagesPeerIdGetQueryKey(
              peerId,
              CHAT_PREVIEW_PARAMS
            )
            queryClient.setQueryData<MessageOutputSchema[]>(previewKey, (old) => {
              if (!old || old.length === 0) return [msg]
              const currentLatest = old[0]
              const isNewer = new Date(msg.created_at) > new Date(currentLatest.created_at)
              return isNewer ? [msg] : old
            })

            // Обновление кэша непрочитанных для входящих сообщений
            if (msg.receiver_id === currentUser.id) {
              const unreadKey = getGetHistoryApiV1SocialMessagesPeerIdGetQueryKey(peerId, UNREAD_CHECK_PARAMS)
              queryClient.setQueryData<MessageOutputSchema[]>(unreadKey, (old) =>
                !old ? [msg] : old.some((m) => m.id === msg.id) ? old : [...old, msg]
              )
            }
          } else if (data.type === 'read') {
            const { message_ids } = data
            
            // Update all message caches (history + preview + unread) to mark messages as read
            queryClient.setQueriesData<MessageOutputSchema[]>(
              { predicate: isMessagesQuery },
              (old) => {
                if (!old) return old
                const hasChanges = old.some((msg) => message_ids.includes(msg.id) && !msg.is_read)
                if (!hasChanges) return old
                
                return old.map((msg) =>
                  message_ids.includes(msg.id)
                    ? { ...msg, is_read: true, read_at: new Date().toISOString() }
                    : msg
                )
              }
            )
          }
        } catch {
          // Ignore parse errors
        }
      }

      ws.onerror = () => {
        socketRef.current = null
        ws.close()
      }

      ws.onclose = () => {
        socketRef.current = null
        if (isMounted) {
          reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 15000)
          reconnectTimeoutRef.current = window.setTimeout(() => {
            if (isMounted) connect()
          }, reconnectDelayRef.current)
        }
      }
    }

    // Ресинк при возврате во вкладку
    let hiddenAt = 0
    const onVisibility = () => {
      if (document.hidden) {
        hiddenAt = Date.now()
        return
      }
      // Вернулись во вкладку
      if (hiddenAt && Date.now() - hiddenAt > 30_000) {
        queryClient.invalidateQueries({ predicate: isMessagesQuery })
      }
      // Если сокет отвалился, переподключаемся
      if (!socketRef.current || socketRef.current.readyState > WebSocket.OPEN) {
        window.clearTimeout(reconnectTimeoutRef.current)
        reconnectDelayRef.current = 1000
        connect()
      }
    }
    document.addEventListener('visibilitychange', onVisibility)

    connect()

    return () => {
      isMounted = false
      document.removeEventListener('visibilitychange', onVisibility)
      if (reconnectTimeoutRef.current !== undefined) {
        window.clearTimeout(reconnectTimeoutRef.current)
      }
      if (socketRef.current) {
        socketRef.current.close()
        socketRef.current = null
      }
    }
  }, [currentUser, queryClient])

  return socketRef
}
