import { formatDistanceToNow } from 'date-fns'
import { ru } from 'date-fns/locale'
import { ArrowBigUp, ArrowBigDown, Pencil, Trash2 } from 'lucide-react'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/lib/utils'
import defaultPfp from '@/assets/defaults/default-pfp.webp'
import { UserLink } from '@/shared/components/UserLink'
import type { ReviewOutputSchema } from '@/api/generated/model'

type CommentItemProps = {
  review: ReviewOutputSchema
  currentUserId?: string
  onEdit: (review: ReviewOutputSchema) => void
  onDelete: (reviewId: string) => void
  isPending: boolean
}

export function CommentItem({ review, currentUserId, onEdit, onDelete, isPending }: CommentItemProps) {
  const isOwn = review.reviewer.id === currentUserId
  const timeAgo = formatDistanceToNow(new Date(review.updated_at), {
    addSuffix: true,
    locale: ru,
  })

  return (
    <div className="flex gap-3">
      <UserLink
        userId={review.reviewer.id}
        username={review.reviewer.username}
        pfpUrl={review.reviewer.pfp_url}
        className="shrink-0"
      >
        <Avatar className="w-9 h-9">
          <AvatarImage src={review.reviewer.pfp_url} alt={review.reviewer.username} />
          <AvatarFallback>
            <img src={defaultPfp} alt="" className="w-full h-full object-cover" />
          </AvatarFallback>
        </Avatar>
      </UserLink>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1 flex-wrap">
          <UserLink
            userId={review.reviewer.id}
            username={review.reviewer.username}
            pfpUrl={review.reviewer.pfp_url}
            className="font-medium text-sm text-foreground hover:underline"
          >
            {review.reviewer.username}
          </UserLink>
          <span
            className={cn(
              'inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full',
              review.rate === 1
                ? 'bg-success/15 text-success'
                : 'bg-destructive/15 text-destructive'
            )}
          >
            {review.rate === 1 ? (
              <>
                <ArrowBigUp className="w-3 h-3 fill-current" />
                Пуш
              </>
            ) : (
              <>
                <ArrowBigDown className="w-3 h-3 fill-current" />
                Шейм
              </>
            )}
          </span>
          <span className="text-xs text-muted-foreground">{timeAgo}</span>
        </div>

        <p className="text-sm text-foreground whitespace-pre-wrap break-words">
          {review.comment}
        </p>

        {isOwn && (
          <div className="flex items-center gap-2 mt-2">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => onEdit(review)}
            >
              <Pencil className="w-3 h-3 mr-1" />
              Изменить
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 px-2 text-xs text-destructive hover:text-destructive"
              onClick={() => onDelete(review.id)}
              disabled={isPending}
            >
              <Trash2 className="w-3 h-3 mr-1" />
              Удалить
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
