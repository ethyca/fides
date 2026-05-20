import React from "react";

import styles from "./SegmentedProgress.module.scss";

const MAX_BLOCKS = 40;

/** A coloured run inside a multi-segment progress bar. */
export interface SegmentedProgressSegment {
  /** Any CSS colour (token, hex, rgba). Applied as the block's background. */
  color: string;
  /** How many segments this run consumes. Values < 1 are ignored. */
  count: number;
}

export interface SegmentedProgressProps {
  /** Total number of segments. */
  total: number;
  /**
   * Number of filled (completed) segments. Used when ``segments`` is not
   * provided — fills with the default ink colour.
   */
  filled?: number;
  /**
   * Multi-colour mode: render each run in order with its own colour, then
   * pad to ``total`` with empty blocks. Overrides ``filled`` when present.
   * Use for categorical breakdowns (e.g. answers grouped by source).
   */
  segments?: SegmentedProgressSegment[];
  /**
   * When true, the first not-yet-filled segment pulses to signal that work is
   * actively in flight (e.g. an agent is generating answers). Has no effect
   * once every segment is filled.
   */
  loading?: boolean;
  className?: string;
}

const scaleCount = (count: number, total: number, displayTotal: number) =>
  total > MAX_BLOCKS
    ? Math.round((count / total) * displayTotal)
    : Math.min(count, total);

/**
 * A discrete progress indicator that renders individual blocks for each item.
 * Filled blocks are dark; empty blocks are light. When `total` exceeds
 * MAX_BLOCKS, the segments are scaled down proportionally.
 *
 * Use ``segments`` for a categorical breakdown (one colour per run) — empty
 * blocks pad to ``total``. Use ``filled`` for the simpler single-colour case.
 */
export const SegmentedProgress: React.FC<SegmentedProgressProps> = ({
  total,
  filled = 0,
  segments,
  loading = false,
  className,
}) => {
  if (total <= 0) {
    return null;
  }

  const displayTotal = Math.min(total, MAX_BLOCKS);
  // Per-block colour: undefined → empty block.
  const blockColors: (string | undefined)[] = [];
  if (segments && segments.length > 0) {
    for (const seg of segments) {
      const scaled = scaleCount(Math.max(0, seg.count), total, displayTotal);
      for (let i = 0; i < scaled && blockColors.length < displayTotal; i += 1) {
        blockColors.push(seg.color);
      }
    }
  } else {
    const displayFilled = scaleCount(filled, total, displayTotal);
    for (let i = 0; i < displayFilled; i += 1) {
      blockColors.push(undefined); // sentinel for "use default filled style"
    }
  }
  // The first un-coloured index is where the loading pulse anchors.
  const firstEmptyIndex = blockColors.length;
  const usingSegments = !!segments && segments.length > 0;

  return (
    <div
      className={`${styles.track} ${className ?? ""}`}
      role="progressbar"
      aria-valuenow={blockColors.length}
      aria-valuemin={0}
      aria-valuemax={total}
      aria-busy={loading || undefined}
    >
      {Array.from({ length: displayTotal }, (_, i) => {
        const color = blockColors[i];
        const isPulsing = loading && i === firstEmptyIndex;
        let modifier = styles.empty;
        if (color !== undefined || (!usingSegments && i < firstEmptyIndex)) {
          modifier = styles.filled;
        }
        if (isPulsing) {
          modifier = styles.pulsing;
        }
        return (
          <div
            key={i}
            className={`${styles.block} ${modifier}`}
            style={color ? { backgroundColor: color } : undefined}
          />
        );
      })}
    </div>
  );
};
