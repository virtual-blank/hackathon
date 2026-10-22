import { useState } from 'react'
import { ArrowBigUp, ArrowBigDown, Send } from 'lucide-react'
import { Button } from '@/shared/ui/button'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/lib/utils'
import { CommentItem } from './CommentItem'
import type { ReviewOutputSchema } from '@/api/generated/model'

type FeedCommentSectionProps = {
  habitId: string
  reviews: ReviewOutputSchema[]
  currentUserId?: string
  myReview?: ReviewOutputSchema
  onSubmitComment: (comment: string, rate: number) => void
  onDeleteReview: (reviewId: string) => void
  isPending: boolean
}

export function FeedCommentSection({
  reviews,
  currentUserId,
  myReview,
  onSubmitComment,
  onDeleteReview,
  isPending,
}: FeedCommentSectionProps) {
  const [commentText, setCommentText] = useState('')
  const [selectedRate, setSelectedRate] = useState<number>(1)
  const [editingReviewId, setEditingReviewId] = useState<string | null>(null)

  const commentsWithText = reviews.filter((r) => r.comment && r.comment.trim().length > 0)

  const handleSubmit = () => {
    if (!commentText.trim()) return

    if (editingReviewId) {
      onSubmitComment(commentText, myReview?.rate ?? 1)
      setEditingReviewId(null)
    } else {
      onSubmitComment(commentText, selectedRate)
    }

    setCommentText('')
  }

  const handleEdit = (review: ReviewOutputSchema) => {
    setCommentText(review.comment || '')
    setSelectedRate(review.rate)
    setEditingReviewId(review.id)
  }

  const handleCancelEdit = () => {
    setCommentText('')
    setEditingReviewId(null)
  }

  return (
    <div className="space-y-4 pt-2 border-t border-border/50">
      {commentsWithText.length > 0 && (
        <div className="space-y-3">
          {commentsWithText.map((review) => (
            <CommentItem
              key={review.id}
              review={review}
              currentUserId={currentUserId}
              onEdit={handleEdit}
              onDelete={onDeleteReview}
              isPending={isPending}
            />
          ))}
        </div>
      )}

      {currentUserId && (
        <div className="space-y-2">
          {!myReview && !editingReviewId && (
            <div className="flex items-center gap-2 text-sm flex-wrap">
              <span className="text-muted-foreground">Тон реакции:</span>
              <button
                onClick={() => setSelectedRate(1)}
                className={cn(
                  'inline-flex items-center gap-1 px-3 py-1 rounded-full border text-xs font-medium transition-all',
                  selectedRate === 1
                    ? 'bg-success/15 text-success border-success/40'
                    : 'border-border hover:bg-muted'
                )}
              >
                <ArrowBigUp className="w-3.5 h-3.5" strokeWidth={2} />
                Пуш
              </button>
              <button
                onClick={() => setSelectedRate(0)}
                className={cn(
                  'inline-flex items-center gap-1 px-3 py-1 rounded-full border text-xs font-medium transition-all',
                  selectedRate === 0
                    ? 'bg-destructive/15 text-destructive border-destructive/40'
                    : 'border-border hover:bg-muted'
                )}
              >
                <ArrowBigDown className="w-3.5 h-3.5" strokeWidth={2} />
                Шейм
              </button>
            </div>
          )}

          <div className="flex items-end gap-2">
            <Textarea
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              placeholder={editingReviewId ? 'Редактировать комментарий...' : 'Напишите комментарий...'}
              className="min-h-[60px] max-h-[120px] resize-none text-sm"
              disabled={isPending}
            />
            <div className="flex flex-col gap-1">
              <Button
                onClick={handleSubmit}
                disabled={!commentText.trim() || isPending}
                size="sm"
                className="h-9 w-9 p-0 shrink-0"
                aria-label="Отправить комментарий"
              >
                <Send className="w-4 h-4" />
              </Button>
              {editingReviewId && (
                <Button
                  onClick={handleCancelEdit}
                  variant="ghost"
                  size="sm"
                  className="h-7 w-9 p-0 shrink-0 text-xs"
                  aria-label="Отменить редактирование"
                >
                  ✕
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
