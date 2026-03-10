import { AnimatePresence, Easing, motion } from "motion/react";
import { ReactNode } from "react";

export interface ExpandCollapseProps {
  /**
   * Whether the content should be expanded (visible) or collapsed (hidden)
   */
  isExpanded: boolean;
  /**
   * The content to be expanded/collapsed
   */
  children: ReactNode;
  /**
   * Duration of the animation in seconds
   * @default 0.3
   */
  duration?: number;
  /**
   * Easing function for the animation
   * @default "easeInOut"
   */
  ease?: Easing | Easing[];
  /**
   * Additional className to apply to the motion wrapper
   */
  className?: string;
  /**
   * Unique key for AnimatePresence. Use this when you have multiple instances
   * that need different animation contexts.
   */
  motionKey?: string;
}

/**
 * A reusable expand/collapse animation component that wraps content
 * with smooth height and opacity transitions.
 *
 * @example
 * ```tsx
 * const [isOpen, setIsOpen] = useState(false);
 *
 * <ExpandCollapse isExpanded={isOpen}>
 *   <div>Content to expand/collapse</div>
 * </ExpandCollapse>
 * ```
 */
export const ExpandCollapse = ({
  isExpanded,
  children,
  duration = 0.3,
  ease = "easeInOut",
  className = "overflow-hidden",
  motionKey = "expand-collapse",
}: ExpandCollapseProps) => (
  <AnimatePresence initial={false}>
    {isExpanded && (
      <motion.div
        key={motionKey}
        initial={{ height: 0, opacity: 0 }}
        animate={{ height: "auto", opacity: 1 }}
        exit={{ height: 0, opacity: 0 }}
        transition={{ duration, ease }}
        className={className}
      >
        {children}
      </motion.div>
    )}
  </AnimatePresence>
);
