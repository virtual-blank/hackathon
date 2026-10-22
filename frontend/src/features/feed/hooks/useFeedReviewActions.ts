import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  useCreateReviewApiV1FeedReviewsPost,
  useEditReviewApiV1FeedReviewsReviewIdPatch,
  useDeleteReviewApiV1FeedReviewsReviewIdDelete,
  getGetFeedApiV1FeedGetQueryKey,
} from '@/api/generated/👁‍🗨-feed/👁‍🗨-feed'
import { getGetDashboardApiV1AnalyticsDashboardGetQueryKey } from '@/api/generated/📊-analytics/📊-analytics'
import type { ReviewOutputSchema } from '@/api/generated/model'

export function useFeedReviewActions(currentUserId?: string) {
  const queryClient = useQueryClient()
  const [pendingDelete, setPendingDelete] = useState<{
    reviewId: string
    habitId: string
  } | null>(null)

  const { mutate: createReview, isPending: isCreating } = useCreateReviewApiV1FeedReviewsPost({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetFeedApiV1FeedGetQueryKey() })
        queryClient.invalidateQueries({ queryKey: getGetDashboardApiV1AnalyticsDashboardGetQueryKey() })
      },
      onError: () => {
        toast.error('Не удалось отправить реакцию')
      },
    },
  })

  const { mutate: editReview, isPending: isEditing } = useEditReviewApiV1FeedReviewsReviewIdPatch({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetFeedApiV1FeedGetQueryKey() })
        queryClient.invalidateQueries({ queryKey: getGetDashboardApiV1AnalyticsDashboardGetQueryKey() })
      },
      onError: () => {
        toast.error('Не удалось изменить реакцию')
      },
    },
  })

  const { mutate: deleteReview, isPending: isDeleting } = useDeleteReviewApiV1FeedReviewsReviewIdDelete({
    mutation: {
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: getGetFeedApiV1FeedGetQueryKey() })
        queryClient.invalidateQueries({ queryKey: getGetDashboardApiV1AnalyticsDashboardGetQueryKey() })
        setPendingDelete(null)
      },
      onError: () => {
        toast.error('Не удалось удалить реакцию')
        setPendingDelete(null)
      },
    },
  })

  const voteReview = (habitId: string, newRate: number, myReview?: ReviewOutputSchema) => {
    if (!currentUserId) {
      toast.error('Войдите, чтобы поставить реакцию')
      return
    }

    if (!myReview) {
      // Create new review with vote only (no comment)
      createReview({
        data: {
          habit_id: habitId,
          rate: newRate,
          comment: null,
        },
      })
    } else {
      // Check if user clicked on the same active vote
      if (myReview.rate === newRate) {
        // If no comment, delete the review immediately
        const hasComment = myReview.comment && myReview.comment.trim().length > 0
        if (!hasComment) {
          deleteReview({ reviewId: myReview.id })
        } else {
          // If there's a comment, ask for confirmation
          setPendingDelete({ reviewId: myReview.id, habitId })
        }
        return
      } else {
        // Switch to opposite vote, preserve comment
        editReview({
          reviewId: myReview.id,
          data: {
            habit_id: habitId,
            rate: newRate,
            comment: myReview.comment || undefined,
          },
        })
      }
    }
  }

  const confirmDelete = () => {
    if (pendingDelete) {
      deleteReview({ reviewId: pendingDelete.reviewId })
    }
  }

  const cancelDelete = () => {
    setPendingDelete(null)
  }

  const submitComment = (
    habitId: string,
    comment: string,
    rate: number,
    myReview?: ReviewOutputSchema
  ) => {
    if (!currentUserId) {
      toast.error('Войдите, чтобы оставить комментарий')
      return
    }

    if (!comment.trim()) {
      toast.error('Комментарий не может быть пустым')
      return
    }

    if (!myReview) {
      // Create new review with comment and selected rate
      createReview({
        data: {
          habit_id: habitId,
          rate,
          comment,
        },
      })
    } else {
      // Update existing review's comment
      editReview({
        reviewId: myReview.id,
        data: {
          habit_id: habitId,
          rate: myReview.rate,
          comment,
        },
      })
    }
  }

  const removeReview = (reviewId: string) => {
    deleteReview({ reviewId })
  }

  return {
    voteReview,
    submitComment,
    removeReview,
    isPending: isCreating || isEditing || isDeleting,
    pendingDelete,
    confirmDelete,
    cancelDelete,
  }
}
