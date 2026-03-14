import { Card, CardProps, theme, Typography } from "antd/lib";
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
   * Font used for the card title.
   * - `"default"`: inherits the theme sans-serif font
   * - `"mono"`: renders the title in the monospace code font
   * @default "default"
   */
  titleFont?: "default" | "mono";
  /**
   * Whether to show the border between the card header and body.
   * @default true
   */
  showTitleDivider?: boolean;
  /**
   * When true, renders the title as a heading and removes the header divider
   * and padding so the title flows with the body.
   * @default false
   */
  titleHeading?: boolean;
}

const withCustomProps = (WrappedComponent: typeof Card) => {
  const WrappedCard = React.forwardRef<HTMLDivElement, CustomCardProps>(
    (
      {
        coverPosition = "top",
        titleFont = "default",
        showTitleDivider = true,
        titleHeading = true,
        className,
        styles: stylesProp,
        title,
        size,
        ...props
      },
      ref,
    ) => {
      const { token } = theme.useToken();

      const effectiveShowDivider = titleHeading ? false : showTitleDivider;

      const headerStyle: React.CSSProperties = effectiveShowDivider
        ? {}
        : { borderBottom: "none" };

      if (titleHeading) {
        const hPad = size === "small" ? token.paddingSM : token.paddingLG;
        headerStyle.minHeight = "unset";
        headerStyle.padding = `${hPad}px ${hPad}px 0`;
      }

      const titleStyle: React.CSSProperties =
        titleFont === "mono"
          ? { fontFamily: token.fontFamilyCode, fontSize: token.fontSize }
          : {};

      const resolvedTitle =
        titleHeading && title ? (
          <Typography.Title level={5} style={{ margin: 0 }}>
            {title}
          </Typography.Title>
        ) : (
          title
        );

      return (
        <WrappedComponent
          ref={ref}
          className={classNames(
            { [styles.bottomCover]: coverPosition === "bottom" },
            { [styles.inlineHeader]: !!props.tabList },
            { [styles.titleHeading]: titleHeading },
            className,
          )}
          title={resolvedTitle}
          size={size}
          styles={{
            ...stylesProp,
            header: { ...headerStyle, ...stylesProp?.header },
            title: { ...titleStyle, ...stylesProp?.title },
          }}
          {...props}
        />
      );
    },
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
 * @param {"default" | "mono"} [titleFont="default"] - Controls the card title font.
 * @param {boolean} [showTitleDivider=true] - Whether to render the border between the
 *   card header and body. Set to `false` to remove the separator line.
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
 *   tabList={[{ key: "a", label: "Tab A" }, { key: "b", label: "Tab B" }]}
 *   activeTabKey={activeTab}
 *   onTabChange={setActiveTab}
 * >
 *   <div>Tab content here</div>
 * </CustomCard>
 */
export const CustomCard = Object.assign(withCustomProps(Card), {
  Meta: Card.Meta,
  Grid: Card.Grid,
});
