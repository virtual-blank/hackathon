export const DASHBOARD_MOTION = {
  easing: [0.22, 1, 0.36, 1] as const,
  expandDuration: 450,
  collapseDuration: 380,
  contentExitDuration: 120,
  contentEnterDelay: 100,
  contentEnterDuration: 260,
  contentEnter: { y: 8, opacity: 0 },
} as const;
