import { useRef } from "react";
import { useMediaQuery } from "@/shared/hooks/use-media-query";
import type { AchievementOutputSchema } from "@/api/generated/model";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/shared/ui/dialog";
import {
  Drawer,
  DrawerContent,
  DrawerTitle,
} from "@/shared/ui/drawer";
import { motion, useMotionValue, useSpring } from "motion/react";
import { VisuallyHidden } from "@radix-ui/react-visually-hidden";
import { resolveAchievementIcon } from "@/shared/lib/achievement-icon";

type AchievementDetailsModalProps = {
  achievement: AchievementOutputSchema;
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

function getRuleTypeLabel(ruleType: string): string {
  const labels: Record<string, string> = {
    STREAK: "Серия дней",
    FRIENDS_COUNT: "Друзья",
    TOTAL_HABITS: "Привычки",
  };
  return labels[ruleType] || ruleType;
}

function Achievement3DView({ achievement }: { achievement: AchievementOutputSchema }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const rotateX = useMotionValue(0);
  const rotateY = useMotionValue(0);

  const springRotateX = useSpring(rotateX, { stiffness: 150, damping: 20 });
  const springRotateY = useSpring(rotateY, { stiffness: 150, damping: 20 });

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const offsetX = e.clientX - centerX;
    const offsetY = e.clientY - centerY;

    const maxTilt = 25;
    const tiltY = -(offsetX / (rect.width / 2)) * maxTilt;
    const tiltX = (offsetY / (rect.height / 2)) * maxTilt;

    rotateX.set(tiltX);
    rotateY.set(tiltY);
  };

  const handlePointerLeave = () => {
    rotateX.set(0);
    rotateY.set(0);
  };

  const iconPath = resolveAchievementIcon(achievement.icon_url);

  return (
    <div
      ref={containerRef}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      className="relative flex items-center justify-center w-full min-h-[280px] overflow-visible"
      style={{ perspective: "900px" }}
    >
      <motion.div
        style={{
          rotateX: springRotateX,
          rotateY: springRotateY,
        }}
        className="relative"
      >
        {/* Glow layer */}
        <motion.div
          className="absolute inset-0 rounded-full blur-[56px] opacity-25"
          style={{
            background: `radial-gradient(circle, ${achievement.color_hex}, transparent 70%)`,
            scale: 1.5,
          }}
        />

        {/* Achievement image */}
        <motion.div className="relative z-10">
          <img
            src={iconPath}
            alt={achievement.name}
            className="w-48 h-48 rounded-full object-cover"
          />

          {/* Glare overlay (cursor follow) */}
          <motion.div
            className="absolute inset-0 rounded-full pointer-events-none"
            style={{
              background: `radial-gradient(circle at ${50 + (springRotateY.get() / 25) * 30}% ${
                  50 - (springRotateX.get() / 25) * 30
                }%, rgba(255, 255, 255, 0.3), transparent 60%)`,
              }}
            />
        </motion.div>
      </motion.div>
    </div>
  );
}

// Export modal component below

export function AchievementDetailsModal({
  achievement,
  open,
  onOpenChange,
}: AchievementDetailsModalProps) {
  const isDesktop = useMediaQuery("(min-width: 1024px)");

  const content = (
    <div className="space-y-6">
      <Achievement3DView achievement={achievement} />

      <div className="text-center space-y-2">
        <h2 className="font-display text-2xl font-semibold">{achievement.name}</h2>
        <p className="text-muted-foreground">{achievement.description}</p>
      </div>

      <div className="space-y-3 p-4 rounded-[12px] bg-surface-muted border border-border">
        <div className="flex items-start gap-4 text-sm">
          <span className="text-muted-foreground shrink-0 w-24">Категория</span>
          <span className="font-medium text-left flex-1">{getRuleTypeLabel(achievement.rule_type)}</span>
        </div>
        <div className="flex items-start gap-4 text-sm">
          <span className="text-muted-foreground shrink-0 w-24">Требование</span>
          <span className="font-medium text-left flex-1 break-words">{achievement.requirement}</span>
        </div>
      </div>
    </div>
  );

  if (isDesktop) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-md">
          <VisuallyHidden>
            <DialogTitle>{achievement.name}</DialogTitle>
          </VisuallyHidden>
          {content}
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent>
        <VisuallyHidden>
          <DrawerTitle>{achievement.name}</DrawerTitle>
        </VisuallyHidden>
        <div className="px-4 pb-8">{content}</div>
      </DrawerContent>
    </Drawer>
  );
}
