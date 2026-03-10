import classNames from "classnames";
import { Easing, HTMLMotionProps, motion } from "motion/react";
import { CSSProperties } from "react";

import styles from "./OpenCloseArrow.module.scss";

export interface OpenCloseArrowProps extends HTMLMotionProps<"i"> {
  /**
   * Whether the arrow is in the "open" state (pointing up ^)
   * When false, the arrow points down (closed state v)
   */
  isOpen: boolean;
  /**
   * Size of the arrow in pixels
   * (fits well with Ant's default font size of 14px)
   * @default 10
   */
  arrowSize?: number;
}

// Ant's ease-in-out cubic-bezier
const ANT_EASE: Easing = [0.645, 0.045, 0.355, 1];

const transition = {
  duration: 0.3,
  ease: ANT_EASE,
};

/**
 * An animated arrow that transitions between pointing down (closed v)
 * and pointing up (open ^). Uses the same animation style
 * as Ant Design's Menu submenu arrow, powered by Framer Motion.
 *
 * @example
 * ```tsx
 * const [isOpen, setIsOpen] = useState(false);
 *
 * <Button
 *   onClick={() => setIsOpen(!isOpen)}
 *   icon={<OpenCloseArrow isOpen={isOpen} />}
 * >
 *   Toggle
 * </Button>
 * ```
 */
export const OpenCloseArrow = ({
  isOpen,
  className,
  arrowSize = 10,
  ...props
}: OpenCloseArrowProps) => {
  const TRANSLATE_X = arrowSize * 0.2;

  return (
    <motion.i
      className={classNames(styles.arrow, className)}
      transition={transition}
      aria-hidden="true"
      style={{ "--arrow-size": `${arrowSize}px` } as CSSProperties}
      {...props}
    >
      {/* Top bar (before) */}
      <motion.span
        className={styles.bar}
        animate={{
          rotate: isOpen ? 45 : -45,
          x: TRANSLATE_X,
        }}
        transition={transition}
      />
      {/* Bottom bar (after) */}
      <motion.span
        className={styles.bar}
        animate={{
          rotate: isOpen ? -45 : 45,
          x: -TRANSLATE_X,
        }}
        transition={transition}
      />
    </motion.i>
  );
};
