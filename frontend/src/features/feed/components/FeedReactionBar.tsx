import { motion } from 'motion/react'
import { ArrowBigUp, ArrowBigDown, MessageSquare } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import type { ReviewOutputSchema } from '@/api/generated/model'

type FeedReactionBarProps = {
  habitId: string
  reviews: ReviewOutputSchema[]
  currentUserId?: string
  myReview?: ReviewOutputSchema
  onVote: (newRate: number) => void
  onToggleComments: () => void
  isPending: boolean
}

export function FeedReactionBar({
  reviews,
  myReview,
  onVote,
  onToggleComments,
  isPending,
}: FeedReactionBarProps) {
  const pushCount = reviews.filter((r) => r.rate === 1).length
  const shameCount = reviews.filter((r) => r.rate === 0).length
  const commentCount = reviews.filter((r) => r.comment && r.comment.trim().length > 0).length

  const isPushActive = myReview?.rate === 1
  const isShameActive = myReview?.rate === 0

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Push button */}
      <motion.button
        whileTap={{ scale: 0.92 }}
        onClick={() => onVote(1)}
        disabled={isPending}
        className={cn(
          'inline-flex items-center gap-2 h-10 px-4 rounded-full border text-sm font-medium transition-all',
          'hover:bg-success/10 hover:text-success hover:border-success/30',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          isPushActive &&
            'bg-success/15 text-success border-success/40 font-semibold shadow-sm'
        )}
        aria-label="Поддержать привычку"
      >
        <ArrowBigUp
          className={cn('w-5 h-5', isPushActive && 'fill-current')}
          strokeWidth={2.25}
        />
        <span>{pushCount}</span>
      </motion.button>

      {/* Shame button */}
      <motion.button
        whileTap={{ scale: 0.92 }}
        onClick={() => onVote(0)}
        disabled={isPending}
        className={cn(
          'inline-flex items-center gap-2 h-10 px-4 rounded-full border text-sm font-medium transition-all',
          'hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          isShameActive &&
            'bg-destructive/15 text-destructive border-destructive/40 font-semibold shadow-sm'
        )}
        aria-label="Пристыдить за невыполнение"
      >
        <ArrowBigDown
          className={cn('w-5 h-5', isShameActive && 'fill-current')}
          strokeWidth={2.25}
        />
        <span>{shameCount}</span>
      </motion.button>

      {/* Comments button */}
      <motion.button
        whileTap={{ scale: 0.92 }}
        onClick={onToggleComments}
        className={cn(
          'inline-flex items-center gap-2 h-10 px-4 rounded-full border text-sm font-medium transition-all',
          'hover:bg-muted hover:border-muted-foreground/20'
        )}
        aria-label="Комментарии"
      >
        <MessageSquare className="w-5 h-5" strokeWidth={1.75} />
        <span>{commentCount}</span>
      </motion.button>
    </div>
  )
}
