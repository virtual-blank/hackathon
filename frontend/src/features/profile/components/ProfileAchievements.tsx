import { useState } from "react";
import type { AchievementOutputSchema } from "@/api/generated/model";
import { resolveAchievementIcon } from "@/shared/lib/achievement-icon";
import { AchievementDetailsModal } from "@/features/habits/components/AchievementDetailsModal";
import { EmptyState } from "@/shared/components/EmptyState";
import { Trophy } from "lucide-react";

type ProfileAchievementsProps = {
  achievements: AchievementOutputSchema[];
};

export function ProfileAchievements({ achievements }: ProfileAchievementsProps) {
  const [selectedAchievement, setSelectedAchievement] = useState<AchievementOutputSchema | null>(null);

  if (achievements.length === 0) {
    return (
      <div className="space-y-4">
        <h2 className="font-display text-2xl font-semibold px-4">Достижения</h2>
        <EmptyState
          title="Пока нет достижений"
          description="Достижения появятся с первыми успехами. Продолжайте выполнять привычки!"
          illustration={<Trophy className="w-16 h-16 text-muted-foreground" strokeWidth={1.5} />}
        />
      </div>
    );
  }

  return (
    <>
      <div className="space-y-4">
        <div className="flex items-center justify-between px-4">
          <h2 className="font-display text-2xl font-semibold">Достижения</h2>
          <span className="text-sm text-muted-foreground">{achievements.length}</span>
        </div>

        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-6 px-4">
          {achievements.map((achievement) => {
            const iconPath = resolveAchievementIcon(achievement.icon_url);

            return (
              <button
                key={achievement.name}
                onClick={() => setSelectedAchievement(achievement)}
                className="group relative flex flex-col items-center transition-transform hover:scale-110 hover:-translate-y-1 motion-reduce:hover:scale-100 motion-reduce:hover:translate-y-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                aria-label={achievement.name}
              >
                {/* Glow layer */}
                <div
                  className="absolute inset-0 rounded-full blur-[24px] opacity-20 group-hover:opacity-35 group-hover:blur-[32px] scale-110 transition-all pointer-events-none motion-reduce:opacity-20"
                  style={{
                    background: `radial-gradient(circle, ${achievement.color_hex} 20%, transparent 65%)`,
                  }}
                />
                
                {/* Icon */}
                <img
                  src={iconPath}
                  alt={achievement.name}
                  className="relative z-10 w-20 h-20 shrink-0 aspect-square object-contain drop-shadow-lg"
                />
              </button>
            );
          })}
        </div>
      </div>

      {selectedAchievement && (
        <AchievementDetailsModal
          achievement={selectedAchievement}
          open={!!selectedAchievement}
          onOpenChange={(open) => !open && setSelectedAchievement(null)}
        />
      )}
    </>
  );
}
