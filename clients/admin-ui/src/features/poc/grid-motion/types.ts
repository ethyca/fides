export const LEFT_CARDS = ["left-1", "left-2", "left-3", "left-4"] as const;

export const CENTER_CARDS = ["health-score", "ai-briefing"] as const;

export const RIGHT_CARDS = [
  "trend-governance-posture",
  "trend-dsr-volume",
  "trend-system-coverage",
  "trend-classification-health",
  "system-coverage",
  "dsr-status",
  "generate-report",
] as const;

export type LeftCardId = (typeof LEFT_CARDS)[number];
export type CenterCardId = (typeof CENTER_CARDS)[number];
export type RightCardId = (typeof RIGHT_CARDS)[number];
export type CardId = LeftCardId | CenterCardId | RightCardId;

// The page-wide single-expand state only targets center + right cards.
// Left cards are governed by their own group state (see GridMotionExperiment).
export type ExpandableCardId = CenterCardId | RightCardId;

export const ALL_CARDS: readonly CardId[] = [
  ...CENTER_CARDS,
  ...LEFT_CARDS,
  ...RIGHT_CARDS,
];
