import { Flex } from "antd/lib";
import { AnimatePresence, Easing, motion } from "motion/react";
import { HTMLAttributes, ReactNode } from "react";

export interface EnterExitListProps<T> extends HTMLAttributes<HTMLDivElement> {
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
   * Gap between items in tailwindcss units (x4)
   */
  gutter?: number;
  /**
   * Duration of the animation in seconds
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
   * Stagger delay between animations in seconds
   * @default 0.05
   * Set to 0 to disable stagger
   */
  stagger?: number;
  /**
   * Distance to slide in/out in pixels
   * @default 100
   */
  slideDistance?: number;
  /**
   * Additional className
   */
  className?: string;
  /**
   * Additional className for the items; avoid using styles that could change the item's position, as they might break the animation
   */
  itemClassName?: string;
}

/**
 * A list component with built-in enter and exit animations for items.
 * Items slide in horizontally from the left and slide out horizontally to the right.
 * Remaining items slide horizontally to fill the gap.
 */
export const EnterExitList = <T,>({
  dataSource,
  renderItem,
  itemKey,
  gutter = 0,
  duration = 0.3,
  bounce = 0.15,
  ease = "easeInOut",
  stagger = 0.05,
  slideDistance = 100,
  itemClassName,
  ...props
}: EnterExitListProps<T>) => {
  return (
    <Flex {...props} gap={gutter} role="list">
      <AnimatePresence mode="popLayout">
        {dataSource.map((item, index) => {
          const key = itemKey(item, index);
          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, x: slideDistance }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: slideDistance }}
              transition={{
                layout: {
                  duration,
                  bounce,
                  ease,
                  delay: stagger > 0 ? index * stagger : 0,
                  type: "spring",
                },
                opacity: {
                  duration: duration * 0.5,
                  ease,
                },
                x: {
                  duration,
                  bounce,
                  ease,
                  delay: stagger > 0 ? index * stagger : 0,
                },
              }}
              layout
              role="listitem"
              className={itemClassName}
            >
              {renderItem(item, index)}
            </motion.div>
          );
        })}
      </AnimatePresence>
    </Flex>
  );
};
