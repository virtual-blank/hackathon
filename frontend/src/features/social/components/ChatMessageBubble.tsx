import { format } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Check, CheckCheck } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import type { MessageOutputSchema } from '@/api/generated/model'

type ChatMessageBubbleProps = {
  message: MessageOutputSchema
  isOwn: boolean
}

export function ChatMessageBubble({ message, isOwn }: ChatMessageBubbleProps) {
  const time = format(new Date(message.created_at), 'HH:mm', { locale: ru })

  return (
    <div className={cn('flex gap-3 items-end', isOwn && 'flex-row-reverse')}>
      <div
        className={cn(
          'max-w-[70%] px-4 py-2.5 text-[15px] leading-snug break-words',
          isOwn
            ? 'bg-primary text-primary-foreground rounded-[16px] rounded-br-[4px]'
            : 'bg-surface-muted text-foreground border border-border rounded-[16px] rounded-bl-[4px]'
        )}
      >
        <p>{message.content}</p>
        <div
          className={cn(
            'flex items-center gap-1 mt-1 text-[12px] opacity-70 font-mono tabular-nums',
            !isOwn && 'text-muted-foreground'
          )}
        >
          <span>{time}</span>
          {isOwn && (
            <span className="ml-1">
              {message.is_read ? <CheckCheck size={14} /> : <Check size={14} />}
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
