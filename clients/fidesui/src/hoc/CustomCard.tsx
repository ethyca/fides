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
  /**
   * Layout of the card header when both a `title` and `tabList` are provided.
   * - `"stacked"`: default Ant Design behaviour (title above tabs)
   * - `"inline"`: title and tabs rendered on the same row, with tabs right-aligned
   * @default "stacked"
   */
  headerLayout?: "stacked" | "inline";
}

const withCustomProps = (WrappedComponent: typeof Card) => {
  const WrappedCard = React.forwardRef<HTMLDivElement, CustomCardProps>(
    (
      { coverPosition = "top", headerLayout = "stacked", className, ...props },
      ref,
    ) => (
      <WrappedComponent
        ref={ref}
        className={classNames(
          { [styles.bottomCover]: coverPosition === "bottom" },
          { [styles.inlineHeader]: headerLayout === "inline" },
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
 * @param {"stacked" | "inline"} [headerLayout="stacked"] - Controls how the card header is
 *   laid out when both a `title` and `tabList` are provided. Use `"inline"` to place the
 *   title and tab bar on the same row, with the tabs right-aligned.
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
 *
 * @example
 * // Card with title left and tabs right-aligned on the same row
 * const [activeTab, setActiveTab] = useState("a");
 * <CustomCard
 *   variant="borderless"
 *   title="Overview"
 *   headerLayout="inline"
 *   tabList={[{ key: "a", label: "Tab A" }, { key: "b", label: "Tab B" }]}
 *   activeTabKey={activeTab}
 *   onTabChange={setActiveTab}
 * >
 *   <div>Tab content here</div>
 * </CustomCard>
 */
export const CustomCard = withCustomProps(Card);
