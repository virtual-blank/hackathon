import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MessageCircle, MoreVertical, Trash2, Ban } from 'lucide-react'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { useFriendActions } from '../hooks/useFriendActions'
import defaultPfp from '@/assets/defaults/default-pfp.webp'
import type { FriendSchema } from '@/api/generated/model'
import type { FriendActivity } from '../hooks/useFriendsActivity'

type FriendRowProps = {
  friend: FriendSchema
  activity: FriendActivity | null
  onNavigateChat: () => void
}

export function FriendRow({
  friend,
  activity,
  onNavigateChat,
}: FriendRowProps) {
  const { deleteFriend, blockUser } = useFriendActions()
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [blockDialogOpen, setBlockDialogOpen] = useState(false)

  const handleDelete = () => {
    deleteFriend.mutate({ friendId: friend.id })
    setDeleteDialogOpen(false)
  }

  const handleBlock = () => {
    blockUser.mutate({ targetId: friend.id })
    setBlockDialogOpen(false)
  }

  return (
    <>
      <div className="h-16 flex items-center gap-3 px-3 -mx-3 rounded-2xl transition-colors hover:bg-muted/60">
        <Link to={`/users/${friend.id}`} state={{ id: friend.id, username: friend.username, pfp_url: friend.pfp_url }} className="flex items-center gap-3 flex-1 min-w-0">
          <div className="relative shrink-0">
            <Avatar className="h-11 w-11">
              <AvatarImage src={friend.pfp_url} alt={friend.username} />
              <AvatarFallback>
                <img src={defaultPfp} alt="" />
              </AvatarFallback>
            </Avatar>
            {activity?.activeToday && (
              <div className="absolute bottom-0 right-0 h-3 w-3 rounded-full bg-success ring-2 ring-surface" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-[15px] font-medium text-foreground truncate">
              {friend.username}
            </p>
            <p className="text-[13px] text-muted-foreground truncate tabular-nums">
              Выполнений за все время: {activity?.totalLogs || 0}
            </p>
          </div>
        </Link>

        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="secondary"
            size="sm"
            onClick={onNavigateChat}
            className="h-9"
          >
            <MessageCircle className="h-4 w-4 mr-1.5" strokeWidth={1.75} />
            Написать
          </Button>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="h-9 w-9 p-0"
                aria-label="Действия"
              >
                <MoreVertical className="h-4 w-4" strokeWidth={1.75} />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => setDeleteDialogOpen(true)}
              >
                <Trash2 className="h-4 w-4 mr-2" strokeWidth={1.75} />
                Удалить из друзей
              </DropdownMenuItem>
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={() => setBlockDialogOpen(true)}
              >
                <Ban className="h-4 w-4 mr-2" strokeWidth={1.75} />
                Заблокировать
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Удалить {friend.username} из друзей?</DialogTitle>
            <DialogDescription>
              Это действие нельзя отменить
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setDeleteDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteFriend.isPending}
            >
              Удалить
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={blockDialogOpen} onOpenChange={setBlockDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Заблокировать {friend.username}?</DialogTitle>
            <DialogDescription>
              Дружба и заявки будут удалены. Отменить блокировку из приложения
              пока нельзя.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setBlockDialogOpen(false)}>
              Отмена
            </Button>
            <Button
              variant="destructive"
              onClick={handleBlock}
              disabled={blockUser.isPending}
            >
              Заблокировать
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
