import classNames from "classnames";
import React from "react";

import styles from "./FidesIndicator.module.scss";

export interface FidesIndicatorProps {
  /** Fill color (any CSS color, including CSS variables). */
  color?: string;
  /** Square size in pixels. Defaults to 8. */
  size?: number;
  /** Adds a colored halo around the indicator (same color as fill). */
  glowing?: boolean;
  /** Subtly pulses opacity + scale to signal in-progress activity. */
  pulsating?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * A small square status indicator. Use to mark categorical state (status
 * badges, risk dots, evaluation freshness) with optional glow or pulse.
 */
export const FidesIndicator: React.FC<FidesIndicatorProps> = ({
  color,
  size = 8,
  glowing = false,
  pulsating = false,
  className,
  style,
}) => (
  <span
    className={classNames(
      styles.indicator,
      { [styles.pulsating]: pulsating },
      className,
    )}
    style={{
      width: size,
      height: size,
      backgroundColor: color,
      boxShadow: glowing && color ? `0 0 6px ${color}` : undefined,
      ...style,
    }}
  />
);
