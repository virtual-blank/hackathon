import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { SendHorizontal } from 'lucide-react'
import { chatMessageSchema, type ChatMessageFormData } from '../lib/schemas'
import { useSendMessage } from '../hooks/useSendMessage'
import { Textarea } from '@/shared/ui/textarea'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/lib/utils'
import { toast } from 'sonner'

type ChatComposerProps = {
  receiverId: string
  socketRef: React.RefObject<WebSocket | null>
}

export function ChatComposer({ receiverId, socketRef }: ChatComposerProps) {
  const { sendMessage, isPending } = useSendMessage(socketRef)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ChatMessageFormData>({
    resolver: zodResolver(chatMessageSchema),
    defaultValues: { content: '' },
  })

  const onSubmit = async (data: ChatMessageFormData) => {
    try {
      await sendMessage(receiverId, data.content)
      reset()
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : 'Не удалось отправить сообщение'
      )
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(onSubmit)()
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="sticky bottom-0 border-t border-border bg-surface p-4"
    >
      <div className="flex items-end gap-3">
        <div className="flex-1">
          <Textarea
            {...register('content')}
            placeholder="Написать сообщение..."
            className={cn(
              'min-h-[44px] max-h-[120px] resize-none bg-surface-muted',
              errors.content && 'border-destructive'
            )}
            onKeyDown={handleKeyDown}
            disabled={isPending}
          />
          {errors.content && (
            <p className="text-sm text-destructive mt-1">{errors.content.message}</p>
          )}
        </div>
        <Button
          type="submit"
          size="icon"
          className="h-11 w-11 shrink-0"
          disabled={isPending}
          aria-label="Отправить сообщение"
        >
          <SendHorizontal size={20} />
        </Button>
      </div>
    </form>
  )
}
