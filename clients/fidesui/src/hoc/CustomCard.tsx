import { Card, CardProps } from "antd/lib";
import classNames from "classnames";
import React from "react";

import styles from "./CustomCard.module.scss";

export interface CustomCardProps extends CardProps {
  /**
   * Position of the cover image/content.
   * - `top`: default Ant Design behaviour (cover above body)
   * - `bottom`: cover rendered below body via CSS order
   * @default "top"
   */
  coverPosition?: "top" | "bottom";
}

const withCustomProps = (WrappedComponent: typeof Card) => {
  const WrappedCard = React.forwardRef<HTMLDivElement, CustomCardProps>(
    ({ coverPosition = "top", className, ...props }, ref) => (
      <WrappedComponent
        ref={ref}
        className={classNames(
          "overflow-clip",
          { [styles.bottomCover]: coverPosition === "bottom" },
          className,
        )}
        {...props}
      />
    ),
  );

  WrappedCard.displayName = "CustomCard";
  return WrappedCard;
};

/**
 * Higher-order component that extends Ant Design's Card with additional layout options.
 *
 * Additional props:
 * @param {"top" | "bottom"} [coverPosition="top"] - Controls where the `cover` content is
 *   displayed relative to the card body. Use `"bottom"` to place a sparkline or chart
 *   below the card content.
 *
 * The component always applies `overflow-clip` so sparkline covers are clipped to the card
 * boundary; pass an additional `className` to extend styling further.
 *
 * @example
 * // Card with a sparkline at the bottom
 * <CustomCard
 *   variant="borderless"
 *   cover={<Sparkline data={data} />}
 *   coverPosition="bottom"
 * >
 *   <Statistic title="Data Sharing" value="15,112,893" />
 * </CustomCard>
 */
export const CustomCard = withCustomProps(Card);
