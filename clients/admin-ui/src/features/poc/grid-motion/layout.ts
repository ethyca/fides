import { CSSProperties } from "react";

import {
  CenterCardId,
  ExpandableCardId,
  RIGHT_CARDS,
  RightCardId,
} from "./types";

type Pos = { col: string; row: string };

const toStyle = (pos: Pos): CSSProperties => ({
  gridColumn: pos.col,
  gridRow: pos.row,
});

const isRight = (id: ExpandableCardId): id is RightCardId =>
  (RIGHT_CARDS as readonly ExpandableCardId[]).includes(id);

/**
 * Right zone (col 9-12). Each card has a pinned home slot and a
 * pinned tray slot. A non-expanded card only moves between its own
 * home and its own tray; cards never swap positions.
 */

const RIGHT_HOME: Record<RightCardId, Pos> = {
  "trend-governance-posture": { col: "9 / span 2", row: "1 / span 2" },
  "trend-dsr-volume": { col: "11 / span 2", row: "1 / span 2" },
  "trend-system-coverage": { col: "9 / span 2", row: "3 / span 2" },
  "trend-classification-health": { col: "11 / span 2", row: "3 / span 2" },
  "system-coverage": { col: "9 / span 2", row: "5 / span 2" },
  "dsr-status": { col: "11 / span 2", row: "5 / span 2" },
  "generate-report": { col: "9 / span 4", row: "7 / span 2" },
};

const RIGHT_TRAY: Record<RightCardId, Pos> = {
  "trend-governance-posture": { col: "9 / span 1", row: "6 / span 1" },
  "trend-dsr-volume": { col: "10 / span 1", row: "6 / span 1" },
  "trend-system-coverage": { col: "11 / span 1", row: "6 / span 1" },
  "trend-classification-health": { col: "12 / span 1", row: "6 / span 1" },
  "system-coverage": { col: "9 / span 2", row: "7 / span 1" },
  "dsr-status": { col: "11 / span 2", row: "7 / span 1" },
  "generate-report": { col: "9 / span 4", row: "8 / span 1" },
};

const EXPANDED_RIGHT: Pos = { col: "9 / span 4", row: "1 / span 5" };

// Center (surface) cards are pinned to the far-left column.
const CENTER: Record<CenterCardId, { compressed: Pos; expanded: Pos }> = {
  "health-score": {
    compressed: { col: "1 / span 4", row: "1 / span 3" },
    expanded: { col: "1 / span 4", row: "1 / span 5" },
  },
  "ai-briefing": {
    compressed: { col: "1 / span 4", row: "6 / span 3" },
    expanded: { col: "1 / span 4", row: "4 / span 5" },
  },
};

export const getCardStyle = (
  cardId: ExpandableCardId,
  expandedCard: ExpandableCardId,
): CSSProperties => {
  const isExpanded = cardId === expandedCard;

  if (isRight(cardId)) {
    if (isExpanded) {
      return toStyle(EXPANDED_RIGHT);
    }
    if (isRight(expandedCard)) {
      return toStyle(RIGHT_TRAY[cardId]);
    }
    return toStyle(RIGHT_HOME[cardId]);
  }

  return toStyle(
    isExpanded ? CENTER[cardId].expanded : CENTER[cardId].compressed,
  );
};
