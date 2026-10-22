import { useState } from 'react'
import { Link } from 'react-router-dom'
import { X, UserPlus, Ban } from 'lucide-react'
import { Avatar, AvatarImage, AvatarFallback } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { Badge } from '@/shared/ui/badge'
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

type RequestRowProps = {
  request: FriendSchema
  type: 'incoming' | 'outgoing'
}

export function RequestRow({ request, type }: RequestRowProps) {
  const { acceptRequest, declineRequest, blockUser } = useFriendActions()
  const [blockDialogOpen, setBlockDialogOpen] = useState(false)

  const handleAccept = () => {
    acceptRequest.mutate({ senderId: request.id })
  }

  const handleDecline = () => {
    declineRequest.mutate({ senderId: request.id })
  }

  const handleBlock = () => {
    blockUser.mutate({ targetId: request.id })
    setBlockDialogOpen(false)
  }

  return (
    <>
      <div className="h-14 flex items-center gap-3 px-3 -mx-3 rounded-2xl transition-colors hover:bg-muted/60">
        <Link to={`/users/${request.id}`} state={{ id: request.id, username: request.username, pfp_url: request.pfp_url }} className="flex items-center gap-3 flex-1 min-w-0">
          <Avatar className="h-9 w-9 shrink-0">
            <AvatarImage src={request.pfp_url} alt={request.username} />
            <AvatarFallback>
              <img src={defaultPfp} alt="" />
            </AvatarFallback>
          </Avatar>

          <p className="flex-1 min-w-0 text-[15px] font-medium text-foreground truncate">
            {request.username}
          </p>
        </Link>

        {type === 'incoming' ? (
          <div className="flex items-center gap-2 shrink-0">
            <Button
              size="sm"
              className="h-8"
              onClick={handleAccept}
              disabled={acceptRequest.isPending}
            >
              <UserPlus className="h-4 w-4 mr-1.5" strokeWidth={1.75} />
              Принять
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={handleDecline}
              disabled={declineRequest.isPending}
              aria-label="Отклонить"
            >
              <X className="h-4 w-4" strokeWidth={1.75} />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  aria-label="Действия"
                >
                  ⋯
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
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
        ) : (
          <Badge variant="secondary" className="shrink-0">
            Ожидает ответа
          </Badge>
        )}
      </div>

      <Dialog open={blockDialogOpen} onOpenChange={setBlockDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Заблокировать {request.username}?</DialogTitle>
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
