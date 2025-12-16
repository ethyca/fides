import classNames from "classnames";
import { AnimatePresence, Easing, motion } from "motion/react";
import { HTMLAttributes, ReactNode } from "react";

export interface ExitGridProps<T> extends HTMLAttributes<HTMLDivElement> {
  /**
   * Array of data items to render
   */
  dataSource: T[];
  /**
   * Function to render each item
   */
  renderItem: (item: T, index: number) => ReactNode;
  /**
   * Function to extract unique key from each item
   */
  itemKey: (item: T, index: number) => string | number;
  /**
   * Number of columns in the grid
   */
  columns: number;
  /**
   * Gap between items in tailwindcss units (x4)
   */
  gutter?: number;
  /**
   * Duration of the exit animation in seconds
   * @default 0.3
   */
  duration?: number;
  /**
   * Bounce factor for the spring animation
   * @default 0.15
   */
  bounce?: number;
  /**
   * Easing function for the animation
   * @default "easeInOut"
   */
  ease?: Easing | Easing[];
  /**
   * Stagger delay between layout animations in seconds
   * @default 0.05
   * Set to 0 to disable stagger
   */
  layoutStagger?: number;
  /**
   * Additional className for the container
   */
  className?: string;
}

/**
 * A grid component with built-in exit animations for items.
 * Items slide vertically and fade out when removed.
 * Remaining items slide horizontally to fill the gap.
 */
export const ExitGrid = <T,>({
  dataSource,
  renderItem,
  itemKey,
  columns = 1,
  gutter = 0,
  duration = 0.3,
  bounce = 0.15,
  ease = "easeInOut",
  layoutStagger = 0.05,
  ...props
}: ExitGridProps<T>) => {
  return (
    <div
      {...props}
      className={classNames(
        props.className,
        "grid",
        `grid-cols-${columns}`,
        `gap-${gutter}`,
      )}
      role="list"
    >
      <AnimatePresence mode="popLayout">
        {dataSource.map((item, index) => {
          const key = itemKey(item, index);
          return (
            <motion.div
              key={key}
              initial={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              transition={{
                layout: {
                  duration,
                  bounce,
                  ease,
                  delay: layoutStagger > 0 ? index * layoutStagger : 0,
                  type: "spring",
                },
              }}
              layout
              role="listitem"
            >
              {renderItem(item, index)}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
};
