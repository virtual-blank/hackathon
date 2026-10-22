import { Heart } from "lucide-react";

type ProfileSupportProps = {
  totalPushesReceived: number;
};

export function ProfileSupport({ totalPushesReceived }: ProfileSupportProps) {
  if (totalPushesReceived === 0) {
    return null;
  }

  return (
    <div className="px-4">
      <div className="p-4 rounded-[12px] bg-surface-muted border border-border flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-success/10 flex items-center justify-center shrink-0">
          <Heart className="w-5 h-5 text-success" strokeWidth={1.75} />
        </div>
        <p className="text-sm text-foreground">
          Получено пушей от друзей: <span className="font-semibold tabular-nums">{totalPushesReceived}</span>
        </p>
      </div>
    </div>
  );
}
