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
}

const withCustomProps = (WrappedComponent: typeof Card) => {
  const WrappedCard = React.forwardRef<HTMLDivElement, CustomCardProps>(
    (
      {
        coverPosition = "top",
        className,
        styles: stylesProp,
        title,
        tabList,
        size,
        ...props
      },
      ref,
    ) => {
      const { token } = theme.useToken();

      // String titles get heading treatment (Typography.Title, collapsed padding).
      // JSX titles pass through unchanged. Header divider is always removed.
      const isStringTitle = typeof title === "string";

      const headerStyle: React.CSSProperties = { borderBottom: "none" };
      if (isStringTitle) {
        const hPad = size === "small" ? token.paddingSM : token.paddingLG;
        headerStyle.minHeight = "unset";
        headerStyle.padding = `${hPad}px ${hPad}px 0`;
      }

      const resolvedTabList = tabList?.map((tab) => ({
        ...tab,
        label: (
          <Typography.Text style={{ fontSize: token.fontSize }}>
            {tab.label}
          </Typography.Text>
        ),
      }));

      const resolvedTitle = isStringTitle ? (
        <Typography.Text strong style={{ fontSize: token.fontSize }}>
          {title}
        </Typography.Text>
      ) : (
        title
      );

      // styles prop can be an object or a function; only spread if it's an object
      const stylesObj =
        typeof stylesProp === "object" && !Array.isArray(stylesProp)
          ? stylesProp
          : undefined;

      return (
        <WrappedComponent
          ref={ref}
          className={classNames(
            { [styles.bottomCover]: coverPosition === "bottom" },
            { [styles.inlineHeader]: !!tabList },
            { [styles.stringTitle]: isStringTitle },
            className,
          )}
          tabList={resolvedTabList}
          title={resolvedTitle}
          size={size}
          styles={{
            ...stylesObj,
            header: { ...headerStyle, ...(stylesObj?.header ?? {}) },
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
 * Extends Ant Design's Card. The header divider is always removed. String titles
 * are wrapped in `<Typography.Text strong>` at `token.fontSize`. JSX titles
 * pass through unchanged. Tab labels are wrapped at `token.fontSizeSM`.
 *
 * @param {"top" | "bottom"} [coverPosition="top"] - Position of the `cover` content
 *   relative to the card body.
 */
export const CustomCard = Object.assign(withCustomProps(Card), {
  Meta: Card.Meta,
  Grid: Card.Grid,
});
