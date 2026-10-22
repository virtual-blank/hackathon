import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  useSendRequestApiV1FriendsRequestsTargetIdPost,
  useAcceptRequestApiV1FriendsSenderIdPost,
  useDeclineRequestApiV1FriendsRequestsSenderIdDelete,
  useDeleteFriendApiV1FriendsFriendIdDelete,
  useBlockUserApiV1FriendsBlocksTargetIdPost,
} from '@/api/generated/🤝-friends/🤝-friends'

export function useFriendActions() {
  const queryClient = useQueryClient()

  const invalidateFriendQueries = () => {
    queryClient.invalidateQueries({ queryKey: ['/api/v1/friends'] })
    queryClient.invalidateQueries({ queryKey: ['/api/v1/friends/requests'] })
  }

  const sendRequest = useSendRequestApiV1FriendsRequestsTargetIdPost({
    mutation: {
      onSuccess: () => {
        invalidateFriendQueries()
      },
      onError: () => {
        toast.error('Не удалось отправить заявку')
      },
    },
  })

  const acceptRequest = useAcceptRequestApiV1FriendsSenderIdPost({
    mutation: {
      onSuccess: () => {
        invalidateFriendQueries()
        toast.success('Заявка принята')
      },
      onError: () => {
        toast.error('Не удалось принять заявку')
      },
    },
  })

  const declineRequest = useDeclineRequestApiV1FriendsRequestsSenderIdDelete({
    mutation: {
      onSuccess: () => {
        invalidateFriendQueries()
        toast.success('Заявка отклонена')
      },
      onError: () => {
        toast.error('Не удалось отклонить заявку')
      },
    },
  })

  const deleteFriend = useDeleteFriendApiV1FriendsFriendIdDelete({
    mutation: {
      onSuccess: () => {
        invalidateFriendQueries()
        toast.success('Друг удалён')
      },
      onError: () => {
        toast.error('Не удалось удалить друга')
      },
    },
  })

  const blockUser = useBlockUserApiV1FriendsBlocksTargetIdPost({
    mutation: {
      onSuccess: () => {
        invalidateFriendQueries()
        toast.success('Пользователь заблокирован')
      },
      onError: () => {
        toast.error('Не удалось заблокировать пользователя')
      },
    },
  })

  return {
    sendRequest,
    acceptRequest,
    declineRequest,
    deleteFriend,
    blockUser,
  }
}
