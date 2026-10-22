import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity, Loader2 } from 'lucide-react'
import { motion } from 'motion/react'
import { useGetFeedApiV1FeedGet } from '@/api/generated/👁‍🗨-feed/👁‍🗨-feed'
import { useGetMeApiV1UsersMeGet } from '@/api/generated/👤-users/👤-users'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { EmptyState } from '@/shared/components/EmptyState'
import { ErrorState } from '@/shared/components/ErrorState'
import { FeedPostCard } from '../components/FeedPostCard'
import { FeedSkeleton } from '../components/FeedSkeleton'
import { useFeedReviewActions } from '../hooks/useFeedReviewActions'

type SortOption = 'all' | 'hot-streaks' | 'discussed'

const PAGE_SIZE = 10

export function FeedPage() {
  const navigate = useNavigate()
  const [sortBy, setSortBy] = useState<SortOption>('all')
  const [limit, setLimit] = useState(PAGE_SIZE)

  const { data: currentUser } = useGetMeApiV1UsersMeGet()
  const {
    data: feed,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useGetFeedApiV1FeedGet(
    { limit, offset: 0 },
    {
      query: {
        placeholderData: (prev) => prev,
      },
    }
  )

  const { voteReview, submitComment, removeReview, isPending, pendingDelete, confirmDelete, cancelDelete } = useFeedReviewActions(
    currentUser?.id
  )

  const sortedFeed = useMemo(() => {
    if (!feed) return []

    const result = [...feed]

    if (sortBy === 'hot-streaks') {
      result.sort((a, b) => b.habit.current_streak_days - a.habit.current_streak_days)
    } else if (sortBy === 'discussed') {
      result.sort((a, b) => (b.reviews?.length || 0) - (a.reviews?.length || 0))
    }

    return result
  }, [feed, sortBy])

  const handleVote = (habitId: string, newRate: number) => {
    const post = feed?.find((p) => p.habit.id === habitId)
    if (!post) return

    const myReview = post.reviews?.find((r) => r.reviewer.id === currentUser?.id)
    voteReview(habitId, newRate, myReview)
  }

  const handleSubmitComment = (habitId: string, comment: string, rate: number) => {
    const post = feed?.find((p) => p.habit.id === habitId)
    if (!post) return

    const myReview = post.reviews?.find((r) => r.reviewer.id === currentUser?.id)
    submitComment(habitId, comment, rate, myReview)
  }

  const handleLoadMore = () => {
    setLimit((prev) => prev + PAGE_SIZE)
  }

  const hasMore = feed && feed.length === limit

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <FeedSkeleton />
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <ErrorState
          title="Не удалось загрузить ленту"
          message="Проверьте подключение к интернету и попробуйте снова"
          onRetry={refetch}
        />
      </div>
    )
  }

  if (!feed || feed.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <EmptyState
          title="Лента пуста"
          description="Добавьте друзей или создайте публичную привычку, чтобы увидеть посты в ленте"
          illustration={
            <div className="w-20 h-20 rounded-full bg-info/10 flex items-center justify-center">
              <Activity className="w-10 h-10 text-info" strokeWidth={1.75} />
            </div>
          }
          actionLabel="Найти друзей"
          onAction={() => navigate('/friends')}
        />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="space-y-4">
        <div>
          <h1 className="font-display text-[32px] font-medium text-foreground leading-tight">
            Лента активности
          </h1>
          <p className="text-muted-foreground text-sm mt-2">
            Следите за прогрессом друзей, поддерживайте пушами или мотивируйте шеймами
          </p>
        </div>

        {/* Sort buttons only */}
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-sm text-muted-foreground">Сортировка:</span>
          <Button
            variant={sortBy === 'all' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('all')}
          >
            Все
          </Button>
          <Button
            variant={sortBy === 'hot-streaks' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('hot-streaks')}
          >
            Горячие стрики
          </Button>
          <Button
            variant={sortBy === 'discussed' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setSortBy('discussed')}
          >
            Обсуждаемые
          </Button>
        </div>
      </div>

      {/* Feed */}
      <motion.div
        className="space-y-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.2 }}
      >
        {sortedFeed.map((post, index) => (
          <motion.div
            key={post.habit.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: index * 0.04 }}
          >
            <FeedPostCard
              post={post}
              currentUserId={currentUser?.id}
              onVote={handleVote}
              onSubmitComment={handleSubmitComment}
              onDeleteReview={removeReview}
              isPending={isPending}
            />
          </motion.div>
        ))}
      </motion.div>

      {/* Load more button */}
      {hasMore && (
        <div className="flex justify-center pt-4">
          <Button
            variant="outline"
            onClick={handleLoadMore}
            disabled={isFetching}
            className="min-w-[140px]"
          >
            {isFetching ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Загрузка...
              </>
            ) : (
              'Показать ещё'
            )}
          </Button>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <Dialog open={!!pendingDelete} onOpenChange={(open) => !open && cancelDelete()}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="font-display text-xl">Удалить реакцию?</DialogTitle>
            <DialogDescription className="text-muted-foreground pt-2">
              Если убрать реакцию, то комментарий тоже будет удален. Продолжить?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={cancelDelete}>
              Отмена
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Удалить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
