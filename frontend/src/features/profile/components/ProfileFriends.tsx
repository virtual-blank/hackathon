import { Link } from "react-router-dom";
import { Avatar, AvatarImage, AvatarFallback } from "@/shared/ui/avatar";
import { Button } from "@/shared/ui/button";
import { EmptyState } from "@/shared/components/EmptyState";
import type { FriendSchema } from "@/api/generated/model";
import { Users } from "lucide-react";
import defaultPfp from "@/assets/defaults/default-pfp.webp";

type ProfileFriendsProps = {
  friends: FriendSchema[];
  isLimited: boolean;
};

export function ProfileFriends({ friends, isLimited }: ProfileFriendsProps) {
  const displayFriends = friends.slice(0, 8);
  const totalCount = isLimited ? "100+" : friends.length.toString();

  if (friends.length === 0) {
    return (
      <div className="space-y-4">
        <h2 className="font-display text-2xl font-semibold px-4">Друзья</h2>
        <EmptyState
          title="Пока нет друзей"
          description="Найдите друзей и следите за их прогрессом"
          actionLabel="Найти друзей"
          onAction={() => {}}
          illustration={<Users className="w-16 h-16 text-muted-foreground" strokeWidth={1.5} />}
        />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between px-4">
        <div className="flex items-baseline gap-2">
          <h2 className="font-display text-2xl font-semibold">Друзья</h2>
          <span className="text-sm text-muted-foreground">{totalCount}</span>
        </div>
        {friends.length > 8 && (
          <Button variant="ghost" size="sm" asChild>
            <Link to="/friends">Все друзья</Link>
          </Button>
        )}
      </div>

      <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 gap-4 px-4">
        {displayFriends.map((friend) => (
          <Link 
            key={friend.id}
            to={`/users/${friend.id}`}
            state={{ id: friend.id, username: friend.username, pfp_url: friend.pfp_url }}
            className="flex flex-col items-center gap-2 text-center transition-opacity hover:opacity-70"
          >
            <Avatar className="w-16 h-16 ring-1 ring-border">
              <AvatarImage src={friend.pfp_url} alt={friend.username} />
              <AvatarFallback>
                <img src={defaultPfp} alt="" className="w-full h-full object-cover" />
              </AvatarFallback>
            </Avatar>
            <span className="text-xs text-muted-foreground truncate w-full">
              {friend.username}
            </span>
          </Link>
        ))}
      </div>
    </div>
  );
}
