import {
  LANE_DOUBLE_COL_MAX,
  LANE_SINGLE_COL_MAX,
  MAX_LANE_COLS,
} from "../constants";

/**
 * Choose a column count for a card group based on its size. The thresholds
 * are tuned for the compliance reading shape — small groups stay 1-column for
 * readability, large groups grow to 3 columns rather than scrolling tall.
 */
export const computeColumnCount = (cardCount: number): number => {
  if (cardCount <= 0) {
    return 1;
  }
  if (cardCount <= LANE_SINGLE_COL_MAX) {
    return 1;
  }
  if (cardCount <= LANE_DOUBLE_COL_MAX) {
    return 2;
  }
  return Math.min(MAX_LANE_COLS, 3);
};
