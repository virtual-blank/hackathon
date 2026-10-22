import { Send, CheckCircle2, Loader2, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/lib/utils'
import { motion } from 'motion/react'

type TelegramStatusCardProps = {
  isConnected: boolean
  onConnect: () => void
  isPending: boolean
  fallbackUrl: string | null
  onClearFallback: () => void
}

export function TelegramStatusCard({
  isConnected,
  onConnect,
  isPending,
  fallbackUrl,
  onClearFallback,
}: TelegramStatusCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
    >
      <Card className="w-full" aria-live="polite">
        <CardHeader>
          <div className="flex items-start gap-4">
            <div
              className={cn(
                'flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-xl transition-colors',
                isConnected
                  ? 'bg-success/10'
                  : 'bg-muted'
              )}
            >
              {isConnected ? (
                <CheckCircle2
                  className="h-5 w-5 text-success"
                  strokeWidth={1.75}
                  aria-hidden="true"
                />
              ) : (
                <Send
                  className="h-5 w-5 text-muted-foreground"
                  strokeWidth={1.75}
                  aria-hidden="true"
                />
              )}
            </div>

            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <h3 className="text-base font-semibold leading-none">
                  Telegram-бот
                </h3>
                {isConnected && (
                  <Badge
                    variant="outline"
                    className="border-success/30 bg-success/10 text-success"
                  >
                    Подключен
                  </Badge>
                )}
              </div>

              <p className="text-sm leading-relaxed text-muted-foreground">
                {isConnected
                  ? 'Напоминания о привычках будут приходить в Telegram.'
                  : 'Подключите Telegram, чтобы получать напоминания о привычках прямо в мессенджере.'}
              </p>
            </div>
          </div>
        </CardHeader>

        {!isConnected && (
          <CardContent className="space-y-3">
            <Button
              onClick={onConnect}
              disabled={isPending}
              className="h-11 w-full"
              aria-label="Привязать Telegram-бот"
            >
              {isPending ? (
                <>
                  <Loader2
                    className="mr-2 h-4 w-4 animate-spin"
                    aria-hidden="true"
                  />
                  Генерация ссылки...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" aria-hidden="true" />
                  Привязать Telegram
                </>
              )}
            </Button>

            {fallbackUrl && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                transition={{ duration: 0.15 }}
                className="overflow-hidden"
              >
                <div className="rounded-lg border border-border bg-surface-muted p-3 space-y-2">
                  <p className="text-xs text-muted-foreground">
                    Откройте ссылку в новой вкладке:
                  </p>
                  <a
                    href={fallbackUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={onClearFallback}
                    className="flex items-center gap-2 text-sm font-medium text-primary hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 rounded"
                  >
                    Открыть бота в Telegram
                    <ExternalLink className="h-3.5 w-3.5" aria-hidden="true" />
                  </a>
                </div>
              </motion.div>
            )}

            <p className="text-xs text-muted-foreground">
              Ссылка действует недолго, откройте её сразу.
            </p>
          </CardContent>
        )}
      </Card>
    </motion.div>
  )
}
