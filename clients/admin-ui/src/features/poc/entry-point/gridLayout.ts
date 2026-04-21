import { CSSProperties } from "react";

import { CardId } from "./types";

const LEFT_CARDS: CardId[] = [
  "priority-actions",
  "risks",
  "privacy-assessments",
  "business-units",
  "activity-feed",
  "ai-agent-activity",
];

const RIGHT_CARDS: CardId[] = [
  "trend-governance-posture",
  "trend-dsr-volume",
  "trend-system-coverage",
  "trend-classification-health",
  "system-coverage",
  "dsr-status",
  "generate-report",
];

// Default compressed positions for all cards
const COMPRESSED: Record<CardId, { col: string; row: string }> = {
  "priority-actions": { col: "1 / span 2", row: "1 / span 2" },
  risks: { col: "3 / span 2", row: "1 / span 2" },
  "privacy-assessments": { col: "1 / span 2", row: "3 / span 2" },
  "business-units": { col: "3 / span 2", row: "3 / span 2" },
  "activity-feed": { col: "1 / span 2", row: "5 / span 2" },
  "ai-agent-activity": { col: "3 / span 2", row: "5 / span 2" },
  "health-score": { col: "5 / span 4", row: "1 / span 3" },
  "ai-briefing": { col: "5 / span 4", row: "4 / span 2" },
  "trend-governance-posture": { col: "9 / span 2", row: "1 / span 2" },
  "trend-dsr-volume": { col: "11 / span 2", row: "1 / span 2" },
  "trend-system-coverage": { col: "9 / span 2", row: "3 / span 2" },
  "trend-classification-health": { col: "11 / span 2", row: "3 / span 2" },
  "system-coverage": { col: "9 / span 2", row: "5 / span 2" },
  "dsr-status": { col: "11 / span 2", row: "5 / span 2" },
  "generate-report": { col: "9 / span 4", row: "7 / span 2" },
};

const COMPRESSED_LEFT_BOTTOM: Array<{ col: string; row: string }> = [
  { col: "1 / span 1", row: "7 / span 1" },
  { col: "2 / span 1", row: "7 / span 1" },
  { col: "3 / span 1", row: "7 / span 1" },
  { col: "4 / span 1", row: "7 / span 1" },
  { col: "1 / span 2", row: "8 / span 1" },
];

const COMPRESSED_RIGHT_BOTTOM: Array<{ col: string; row: string }> = [
  { col: "9 / span 1", row: "7 / span 1" },
  { col: "10 / span 1", row: "7 / span 1" },
  { col: "11 / span 1", row: "7 / span 1" },
  { col: "12 / span 1", row: "7 / span 1" },
  { col: "9 / span 2", row: "8 / span 1" },
  { col: "11 / span 2", row: "8 / span 1" },
];

export function getCardStyle(
  cardId: CardId,
  expandedCard: CardId,
): CSSProperties {
  const isLeft = LEFT_CARDS.includes(cardId);
  const isRight = RIGHT_CARDS.includes(cardId);
  const expandedIsLeft = LEFT_CARDS.includes(expandedCard);
  const expandedIsRight = RIGHT_CARDS.includes(expandedCard);

  // This card IS the expanded card
  if (cardId === expandedCard) {
    if (isLeft) {
      return { gridColumn: "1 / span 4", gridRow: "1 / span 6" };
    }
    if (cardId === "health-score") {
      return { gridColumn: "4 / span 5", gridRow: "1 / span 5" };
    }
    if (cardId === "ai-briefing") {
      return { gridColumn: "4 / span 5", gridRow: "2 / span 6" };
    }
    if (isRight) {
      return { gridColumn: "9 / span 4", gridRow: "1 / span 6" };
    }
  }

  // This card is NOT the expanded card

  // A left card while another left card is expanded → compress to bottom row
  if (expandedIsLeft && isLeft) {
    const otherLeftCards = LEFT_CARDS.filter((id) => id !== expandedCard);
    const index = otherLeftCards.indexOf(cardId);
    const pos =
      index >= 0 && index < COMPRESSED_LEFT_BOTTOM.length
        ? COMPRESSED_LEFT_BOTTOM[index]
        : COMPRESSED[cardId];
    return { gridColumn: pos.col, gridRow: pos.row };
  }

  // A right card while another right card is expanded → compress to bottom row
  if (expandedIsRight && isRight) {
    const otherRightCards = RIGHT_CARDS.filter((id) => id !== expandedCard);
    const index = otherRightCards.indexOf(cardId);
    const pos =
      index >= 0 && index < COMPRESSED_RIGHT_BOTTOM.length
        ? COMPRESSED_RIGHT_BOTTOM[index]
        : COMPRESSED[cardId];
    return { gridColumn: pos.col, gridRow: pos.row };
  }

  // All other cases: use default compressed position
  const pos = COMPRESSED[cardId];
  return { gridColumn: pos.col, gridRow: pos.row };
}
