import classNames from "classnames";
import { CSSProperties, ReactNode } from "react";

import styles from "./IconBadge.module.scss";

export interface IconBadgeProps {
  /**
   * The icon to display inside the badge.
   */
  children: ReactNode;
  /**
   * Badge shape.
   * @default "square"
   */
  shape?: "circle" | "square";
  /**
   * `outlined` renders a bordered transparent badge using the Ant border token.
   * `filled` renders a solid-color badge with a white icon.
   * @default "outlined"
   */
  variant?: "outlined" | "filled";
  /**
   * Width and height of the badge in pixels.
   * @default 32
   */
  size?: number;
  /**
   * Background color for the `filled` variant. Accepts any valid CSS color value,
   * including CSS custom properties (e.g. `var(--fidesui-success)`).
   */
  color?: string;
  className?: string;
}

/**
 * A small container that wraps an icon in a consistently-sized circle or
 * rounded-square badge. Useful for template icons, status indicators, and
 * similar decorative icon treatments.
 *
 * @example
 * // Outlined square (default) — e.g. template icon
 * <IconBadge size={40}><Icons.Document /></IconBadge>
 *
 * @example
 * // Filled circle — e.g. success checkmark
 * <IconBadge shape="circle" variant="filled" color="var(--fidesui-success)" size={28}>
 *   <Icons.Checkmark size={14} />
 * </IconBadge>
 */
export const IconBadge = ({
  children,
  shape = "square",
  variant = "outlined",
  size = 32,
  color,
  className,
}: IconBadgeProps) => {
  const style: CSSProperties = {
    width: size,
    height: size,
    ...(variant === "filled" && color ? { backgroundColor: color } : {}),
  };

  return (
    <span
      className={classNames(
        styles.root,
        styles[shape],
        styles[variant],
        className,
      )}
      style={style}
    >
      {children}
    </span>
  );
};
