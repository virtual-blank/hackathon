import { useState, useEffect, useRef } from 'react'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { useGenerateTelegramLinkApiV1TelegramLinkPost } from '@/api/generated/📱-telegram/📱-telegram'
import { Button } from '@/shared/ui/button'
import { Check, Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { SettingsSection, SettingsRow } from './SettingsSection'

export function IntegrationsSection() {
  const { data: me, refetch } = useGetMeApiV1UsersMeGet()
  const { mutate: generateLink, isPending } = useGenerateTelegramLinkApiV1TelegramLinkPost()
  const [waiting, setWaiting] = useState(false)
  const [linkUrl, setLinkUrl] = useState<string | null>(null)
  const timerRef = useRef<number | undefined>(undefined)
  const prevChatIdRef = useRef<number | null>(me?.telegram_chat_id ?? null)

  // Polling while waiting
  useEffect(() => {
    if (waiting) {
      const startTime = Date.now()
      timerRef.current = window.setInterval(() => {
        if (Date.now() - startTime > 120000) {
          setWaiting(false)
          clearInterval(timerRef.current)
          return
        }
        refetch()
      }, 3000)
    }
    return () => clearInterval(timerRef.current)
  }, [waiting, refetch])

  // Stop polling when chat_id appears
  useEffect(() => {
    const prev = prevChatIdRef.current
    const current = me?.telegram_chat_id ?? null
    prevChatIdRef.current = current

    if (waiting && !prev && current) {
      setWaiting(false)
      toast.success('Telegram подключён')
      clearInterval(timerRef.current)
    }
  }, [me?.telegram_chat_id, waiting])

  const handleConnect = () => {
    generateLink(undefined, {
      onSuccess: (data) => {
        setLinkUrl(data.url)
        window.open(data.url, '_blank', 'noopener,noreferrer')
        setWaiting(true)
      },
      onError: () => toast.error('Не удалось получить ссылку'),
    })
  }

  const isConnected = me?.telegram_chat_id != null

  return (
    <SettingsSection title="Интеграции">
      <SettingsRow
        label="Telegram"
        description="Привяжите Telegram-бота для уведомлений"
        isLast
      >
        <div className="flex items-center gap-2">
          {isConnected ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-success/10 text-success">
              <Check className="w-4 h-4" />
              <span className="text-sm font-medium">Подключён</span>
            </div>
          ) : waiting ? (
            <>
              <Button variant="secondary" size="sm" disabled>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Ждём подтверждения…
              </Button>
              {linkUrl && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => window.open(linkUrl, '_blank')}
                >
                  Открыть бота снова
                </Button>
              )}
            </>
          ) : (
            <>
              <div className="px-3 py-1.5 rounded-full bg-muted text-muted-foreground text-sm font-medium">
                Не подключён
              </div>
              <Button
                variant="default"
                size="sm"
                onClick={handleConnect}
                disabled={isPending}
              >
                {isPending ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : null}
                Подключить
              </Button>
            </>
          )}
        </div>
      </SettingsRow>
      {isConnected && (
        <div className="px-4 pb-3 text-xs text-muted-foreground">
          Чтобы отвязать бота, остановите его в Telegram
        </div>
      )}
    </SettingsSection>
  )
}
