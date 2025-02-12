import { Tag, TagProps } from "antd/lib";
import React from "react";

import palette from "../palette/palette.module.scss";

// Extract brand colors that start with "FIDESUI_BG_" from palette
type BrandColorKeys = keyof typeof palette;
type BgColorKeys = Extract<BrandColorKeys, `FIDESUI_BG_${string}`>;
type ColorName = BgColorKeys extends `FIDESUI_BG_${infer Name}` ? Name : never;

// Create a union type of all available brand colors (without the bg- prefix)
export type BrandColor = Lowercase<ColorName> | "transparent";

interface CustomTagProps extends Omit<TagProps, "color"> {
  color?: TagProps["color"] | BrandColor;
}

// Colors that need light text and border
const DARK_BACKGROUNDS = ["minos"];

/**
 * Higher-order component that adds brand colors support to the Tag component.
 */
const withCustomProps = (WrappedComponent: typeof Tag) => {
  const WrappedTag = ({
    color = "corinth",
    style,
    ...props
  }: CustomTagProps) => {
    // If it's a brand color, use our palette
    const brandColor =
      typeof color === "string" &&
      color !== "transparent" &&
      `FIDESUI_BG_${color.toUpperCase()}` in palette
        ? (`FIDESUI_BG_${color.toUpperCase()}` as BgColorKeys)
        : undefined;
    const needsLightText = color && DARK_BACKGROUNDS.includes(color);
    let customStyle = {};
    if (brandColor) {
      customStyle = {
        backgroundColor: palette[brandColor],
        color: needsLightText ? palette.FIDESUI_NEUTRAL_100 : undefined,
      };
    } else if (color === "transparent") {
      customStyle = {
        backgroundColor: "transparent",
      };
    }

    // If not a brand color, pass through to Ant Tag
    const customProps = {
      color: brandColor || color === "transparent" ? undefined : color,
      style: { ...style, ...customStyle },
      ...props,
    };

    return <WrappedComponent {...customProps} />;
  };
  return WrappedTag;
};

export const CustomTag = withCustomProps(Tag);
