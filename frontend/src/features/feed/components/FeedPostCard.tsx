import { useState, useMemo } from 'react'
import { format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'
import { Users, Globe } from 'lucide-react'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import defaultPfp from '@/assets/defaults/default-pfp.webp'
import { HabitPostHeatmap } from './HabitPostHeatmap'
import { FeedReactionBar } from './FeedReactionBar'
import { FeedCommentSection } from './FeedCommentSection'
import { pluralizeCount } from '../lib/pluralize'
import { UserLink } from '@/shared/components/UserLink'
import type { FeedOutputSchema } from '@/api/generated/model'

type FeedPostCardProps = {
  post: FeedOutputSchema
  currentUserId?: string
  onVote: (habitId: string, newRate: number) => void
  onSubmitComment: (habitId: string, comment: string, rate: number) => void
  onDeleteReview: (reviewId: string) => void
  isPending: boolean
}

export function FeedPostCard({
  post,
  currentUserId,
  onVote,
  onSubmitComment,
  onDeleteReview,
  isPending,
}: FeedPostCardProps) {
  const [commentsExpanded, setCommentsExpanded] = useState(false)

  const { creator, habit, total_logs_count, habit_logs, reviews = [] } = post

  const myReview = useMemo(
    () => reviews.find((r) => r.reviewer.id === currentUserId),
    [reviews, currentUserId]
  )

  const startDateFormatted = format(parseISO(habit.start_date), 'd MMM', { locale: ru })

  return (
    <div
      className="rounded-[20px] border border-border bg-surface p-5 md:p-6 space-y-5 transition-all"
      style={
        {
          '--habit': habit.color_hex,
          boxShadow: `0 4px 18px color-mix(in srgb, var(--habit) 14%, transparent)`,
        } as React.CSSProperties
      }
    >
      {/* Header */}
      <div className="flex items-center gap-3 flex-wrap">
        <UserLink
          userId={creator.id}
          username={creator.username}
          pfpUrl={creator.pfp_url}
          className="flex items-center gap-3 flex-1 min-w-0"
        >
          <Avatar className="w-11 h-11 shrink-0">
            <AvatarImage src={creator.pfp_url} alt={creator.username} />
            <AvatarFallback>
              <img src={defaultPfp} alt="" className="w-full h-full object-cover" />
            </AvatarFallback>
          </Avatar>

          <div className="flex-1 min-w-0">
            <div className="font-sans font-semibold text-sm text-foreground hover:underline">
              {creator.username}
            </div>
            <div className="text-xs text-muted-foreground">Старт: {startDateFormatted}</div>
          </div>
        </UserLink>

        <div className="inline-flex items-center px-2 py-1 rounded-full bg-muted text-muted-foreground text-xs">
          {habit.visibility === 'friends' ? (
            <Users className="w-3.5 h-3.5" strokeWidth={1.75} />
          ) : (
            <Globe className="w-3.5 h-3.5" strokeWidth={1.75} />
          )}
        </div>
      </div>

      {/* Title and stats */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <div
            className="w-1.5 h-7 rounded-full shrink-0"
            style={{
              backgroundColor: habit.color_hex,
              boxShadow: `0 0 8px ${habit.color_hex}60`,
            }}
          />
          <h3 className="font-sans font-semibold text-lg text-foreground flex-1">
            {habit.title}
          </h3>
        </div>
        <div className="text-sm text-muted-foreground ml-5">
          Выполнено {total_logs_count} {pluralizeCount(total_logs_count)}
        </div>
      </div>

      {/* Heatmap */}
      <HabitPostHeatmap
        habit={habit}
        habitLogs={habit_logs}
        totalLogsCount={total_logs_count}
      />

      {/* Reaction bar */}
      <FeedReactionBar
        habitId={habit.id}
        reviews={reviews}
        currentUserId={currentUserId}
        myReview={myReview}
        onVote={(newRate) => onVote(habit.id, newRate)}
        onToggleComments={() => setCommentsExpanded(!commentsExpanded)}
        isPending={isPending}
      />

      {/* Comment section */}
      {commentsExpanded && (
        <FeedCommentSection
          habitId={habit.id}
          reviews={reviews}
          currentUserId={currentUserId}
          myReview={myReview}
          onSubmitComment={(comment, rate) => onSubmitComment(habit.id, comment, rate)}
          onDeleteReview={onDeleteReview}
          isPending={isPending}
        />
      )}
    </div>
  )
}
