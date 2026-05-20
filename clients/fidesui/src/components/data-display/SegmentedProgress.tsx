import React from "react";

import styles from "./SegmentedProgress.module.scss";

const MAX_BLOCKS = 40;

export interface SegmentedProgressProps {
  /** Total number of segments. */
  total: number;
  /** Number of filled (completed) segments. */
  filled: number;
  /**
   * When true, the first not-yet-filled segment pulses to signal that work is
   * actively in flight (e.g. an agent is generating answers). Has no effect
   * once every segment is filled.
   */
  loading?: boolean;
  className?: string;
}

/**
 * A discrete progress indicator that renders individual blocks for each item.
 * Filled blocks are dark; empty blocks are light. When `total` exceeds
 * MAX_BLOCKS, the segments are scaled down proportionally.
 */
export const SegmentedProgress: React.FC<SegmentedProgressProps> = ({
  total,
  filled,
  loading = false,
  className,
}) => {
  if (total <= 0) {
    return null;
  }

  const displayTotal = Math.min(total, MAX_BLOCKS);
  const displayFilled =
    total > MAX_BLOCKS
      ? Math.round((filled / total) * MAX_BLOCKS)
      : Math.min(filled, total);

  return (
    <div
      className={`${styles.track} ${className ?? ""}`}
      role="progressbar"
      aria-valuenow={filled}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-busy={loading || undefined}
    >
      {Array.from({ length: displayTotal }, (_, i) => {
        let modifier = styles.empty;
        if (i < displayFilled) {
          modifier = styles.filled;
        } else if (loading && i === displayFilled) {
          modifier = styles.pulsing;
        }
        return <div key={i} className={`${styles.block} ${modifier}`} />;
      })}
    </div>
  );
};
