import { Tag, TagProps } from "antd/lib";
import { Icons } from "fidesui";
import React from "react";

import SparkleIcon from "../icons/Sparkle";
import palette from "../palette/palette.module.scss";
import styles from "./CustomTag.module.scss";

// Extract brand colors that start with "FIDESUI_BG_" from palette
type BrandColorKeys = keyof typeof palette;
type BgColorKeys = Extract<BrandColorKeys, `FIDESUI_BG_${string}`>;
type ColorName = BgColorKeys extends `FIDESUI_BG_${infer Name}` ? Name : never;

// Create a union type of all available brand colors (without the bg- prefix)
export type BrandColor = Lowercase<ColorName> | "transparent";

interface CustomTagProps extends Omit<TagProps, "color"> {
  color?: TagProps["color"] | BrandColor;
  addable?: boolean;
  hasSparkle?: boolean;
}

// Colors that need light text and border
const DARK_BACKGROUNDS = ["minos"];
const RETAIN_DEFAULT_BORDER = ["corinth", "transparent"];

/**
 * Higher-order component that adds brand colors support to the Tag component.
 */
const withCustomProps = (WrappedComponent: typeof Tag) => {
  const WrappedTag = ({
    onClick,
    color = onClick ? "transparent" : "default",
    style,
    children,
    addable,
    hasSparkle,
    ...props
  }: CustomTagProps) => {
    const hasOnlyIcon =
      React.Children.count(children) === 1 &&
      React.isValidElement(children) &&
      typeof children.type === "object";

    const shouldReducePadding = hasOnlyIcon || (addable && !children);

    // If it's a brand color, use our palette
    const brandColor =
      typeof color === "string" &&
      color !== "transparent" &&
      `FIDESUI_BG_${color.toUpperCase()}` in palette
        ? (`FIDESUI_BG_${color.toUpperCase()}` as BgColorKeys)
        : undefined;
    const needsLightText = color && DARK_BACKGROUNDS.includes(color);
    const retainDefaultBorder = color && RETAIN_DEFAULT_BORDER.includes(color);
    let customStyle = {};
    if (brandColor) {
      customStyle = {
        background: palette[brandColor],
        color: needsLightText ? palette.FIDESUI_NEUTRAL_100 : undefined,
      };
    } else if (color === "transparent") {
      customStyle = {
        background: "transparent",
      };
    }

    // If not a brand color, pass through to Ant Tag
    const customProps: TagProps = {
      color: brandColor || color === "transparent" ? undefined : color,
      style: {
        ...style,
        ...customStyle,
        marginInlineEnd: 0, // allow for flex gap instead of margin
        paddingInline: shouldReducePadding
          ? "calc((var(--ant-padding-xs) * 0.5) - 1px)" // -1px to account for border
          : undefined,
      },
      className: styles.tag,
      bordered: retainDefaultBorder,
      closeIcon: props.closable ? <Icons.CloseLarge size={10} /> : undefined,
      children: (
        <>
          {hasSparkle && <SparkleIcon />}
          {children}
          {addable && <Icons.AddLarge size={10} aria-label="Add" />}
        </>
      ),
      ...props,
    };

    return onClick ? (
      <button type="button" onClick={onClick} className={styles.buttonTag}>
        <WrappedComponent {...customProps} />
      </button>
    ) : (
      <WrappedComponent {...customProps} />
    );
  };
  return WrappedTag;
};

export const CustomTag = withCustomProps(Tag);
