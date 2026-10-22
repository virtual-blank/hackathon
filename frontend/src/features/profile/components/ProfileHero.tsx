import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { Avatar, AvatarImage, AvatarFallback } from "@/shared/ui/avatar";
import { pluralizeDays } from "@/shared/lib/date";
import { pluralize } from "@/shared/lib/pluralize";
import type { UserOutputSchema, HabitOutputSchema } from "@/api/generated/model";
import type { AudienceType } from "../lib/profile-helpers";
import { AudienceSwitch } from "./AudienceSwitch";
import defaultPfp from "@/assets/defaults/default-pfp.webp";

type ProfileHeroProps = {
  user: UserOutputSchema;
  friendsCount: number;
  visibleHabitsCount: number;
  bestStreak: number;
  totalCompletions: number;
  brightestHabit: HabitOutputSchema | null;
  audience: AudienceType;
  onAudienceChange: (value: AudienceType) => void;
};

export function ProfileHero({
  user,
  friendsCount,
  visibleHabitsCount,
  bestStreak,
  totalCompletions,
  brightestHabit,
  audience,
  onAudienceChange,
}: ProfileHeroProps) {
  const memberSince = format(new Date(user.created_at), "MMMM yyyy", { locale: ru });
  const habitColor = brightestHabit?.color_hex || null;

  return (
    <div className="relative">
      {/* Subtle glow from brightest habit */}
      {habitColor && (
        <div
          className="absolute inset-0 rounded-[24px] pointer-events-none opacity-[0.08] blur-[64px]"
          style={{
            background: `radial-gradient(circle at 50% 30%, ${habitColor}, transparent 60%)`,
          }}
        />
      )}

      <div className="relative px-4 py-8 space-y-6">
        {/* Avatar and username */}
        <div className="flex flex-col items-center gap-3">
          <Avatar className="w-24 h-24 lg:w-[120px] lg:h-[120px] ring-2 ring-border">
            <AvatarImage src={user.pfp_url || defaultPfp} alt={user.username} />
            <AvatarFallback className="text-2xl lg:text-3xl">
              {user.username[0]?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div className="text-center space-y-1">
            <h1 className="font-display text-3xl lg:text-4xl font-semibold">{user.username}</h1>
            <p className="text-sm text-muted-foreground">С нами с {memberSince}</p>
          </div>
        </div>

        {/* Metrics row */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 max-w-2xl mx-auto">
          <div className="text-center space-y-1">
            <div className="font-display text-3xl font-semibold tabular-nums">{friendsCount}</div>
            <div className="text-xs text-muted-foreground">
              {pluralize(friendsCount, "Друг", "Друга", "Друзей")}
            </div>
          </div>
          <div className="text-center space-y-1">
            <div className="font-display text-3xl font-semibold tabular-nums">
              {visibleHabitsCount}
            </div>
            <div className="text-xs text-muted-foreground">
              {pluralize(visibleHabitsCount, "Привычка", "Привычки", "Привычек")}
            </div>
          </div>
          <div className="text-center space-y-1">
            <div className="font-display text-3xl font-semibold tabular-nums">
              {bestStreak} {pluralizeDays(bestStreak)}
            </div>
            <div className="text-xs text-muted-foreground">Лучшая серия</div>
          </div>
          <div className="text-center space-y-1">
            <div className="font-display text-3xl font-semibold tabular-nums">{totalCompletions}</div>
            <div className="text-xs text-muted-foreground">
              {pluralize(totalCompletions, "Отметка", "Отметки", "Отметок")}
            </div>
          </div>
        </div>

        {/* Audience switch */}
        <AudienceSwitch value={audience} onChange={onAudienceChange} className="mt-4" />
      </div>
    </div>
  );
}
