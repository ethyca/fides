import { Tag, TagProps } from "antd/lib";
import { Icons } from "fidesui";
import React, { useEffect, useRef } from "react";

import SparkleIcon from "../icons/Sparkle";
import palette from "../palette/palette.module.scss";
import styles from "./CustomTag.module.scss";

// eslint-disable-next-line @typescript-eslint/naming-convention
export enum CUSTOM_TAG_COLOR {
  DEFAULT = "default",
  CORINTH = "corinth",
  MINOS = "minos",
  NECTAR = "nectar",
  OLIVE = "olive",
  SANDSTONE = "sandstone",
  TERRACOTTA = "terracotta",
  MARBLE = "marble",
  ERROR = "error",
  WARNING = "warning",
  INFO = "info",
  SUCCESS = "success",
  ALERT = "alert",
  CAUTION = "caution",
  WHITE = "white",
}

// Derive BrandColor from the enum to avoid duplication
type BrandColor = `${CUSTOM_TAG_COLOR}`;

export interface CustomTagProps extends Omit<TagProps, "color"> {
  color?: BrandColor;
  addable?: boolean;
  hasSparkle?: boolean;
  closeButtonLabel?: string;
}

// Colors that need light text and border
const DARK_BACKGROUNDS = ["minos"];
const RETAIN_DEFAULT_BORDER = ["corinth", "white"];

/**
 * Higher-order component that adds brand colors support to the Tag component.
 */
const withCustomProps = (WrappedComponent: typeof Tag) => {
  const WrappedTag = React.forwardRef<HTMLElement, CustomTagProps>(
    (
      {
        onClick,
        color = onClick ? CUSTOM_TAG_COLOR.WHITE : CUSTOM_TAG_COLOR.DEFAULT,
        style,
        className,
        addable,
        hasSparkle,
        closeButtonLabel = "Remove",
        ...props
      },
      forwardedRef,
    ) => {
      const internalRef = useRef<HTMLElement>(null);
      // Merge internal ref with forwarded ref
      const tagRef = forwardedRef || internalRef;

      const hasOnlyIcon =
        React.Children.count(props.children) === 1 &&
        React.isValidElement(props.children) &&
        typeof props.children.type === "object";

      const shouldReducePadding = hasOnlyIcon || (addable && !props.children);

      // Update aria-label post-render to override Ant Design's aggresive default "Close"
      useEffect(() => {
        if (
          (props.closable ?? props.onClose) &&
          closeButtonLabel !== "Remove" &&
          tagRef &&
          "current" in tagRef &&
          tagRef.current
        ) {
          // Find the close button within the tag
          const closeButton = tagRef.current.querySelector(
            ".ant-tag-close-icon",
          );
          if (closeButton) {
            closeButton.setAttribute("aria-label", closeButtonLabel);
          }
        }
      }, [props.closable, props.onClose, closeButtonLabel, tagRef]);

      // If it's a brand color, use our palette
      const brandColor: string | undefined =
        typeof color === "string" &&
        `FIDESUI_BG_${color.toUpperCase()}` in palette
          ? `FIDESUI_BG_${color.toUpperCase()}`
          : undefined;
      const needsLightText = color && DARK_BACKGROUNDS.includes(color);
      const retainDefaultBorder =
        !!color && RETAIN_DEFAULT_BORDER.includes(color);
      let customStyle = {};
      if (brandColor) {
        customStyle = {
          background: palette[brandColor],
          color: needsLightText ? palette.FIDESUI_NEUTRAL_100 : undefined,
        };
      }

      const customProps: TagProps = {
        // If not a brand color, pass through to Ant Tag
        color: brandColor ? undefined : color,
        style: {
          ...customStyle,
          marginInlineEnd: 0, // allow for flex gap instead of margin
          paddingInline: shouldReducePadding
            ? "calc((var(--ant-padding-xs) * 0.5))"
            : undefined,
          ...style,
        },
        className: `${styles.tag} ${className ?? ""}`.trim(),
        bordered: retainDefaultBorder,
        ...props,
        closeIcon:
          (props.closable ?? props.onClose) ? (
            // Ant's own close icon doesn't currently use a button element,
            // so we need to use our own for accessibility.
            //
            // NOTE: Ant Design overrides aria-label with "Close" no matter what,
            // but we fix this post-render using useEffect above.
            <button
              type="button"
              className={styles.closeButton}
              aria-label={closeButtonLabel}
            >
              {props.closeIcon ?? <Icons.CloseLarge size={12} />}
            </button>
          ) : undefined,
        children: (
          <>
            {hasSparkle && <SparkleIcon />}
            {props.children}
            {addable && (
              <Icons.AddLarge
                size={10}
                aria-label={props["aria-label"] || "Add"}
              />
            )}
          </>
        ),
      };

      return onClick ? (
        <button type="button" onClick={onClick} className={styles.buttonTag}>
          <WrappedComponent {...customProps} ref={tagRef} data-color={color} />
        </button>
      ) : (
        <WrappedComponent {...customProps} ref={tagRef} data-color={color} />
      );
    },
  );

  WrappedTag.displayName = "CustomTag";
  return WrappedTag;
};

/**
 * CustomTag extends Ant Design's Tag component with Fides brand colors and enhanced functionality.
 * It provides consistent styling and behavior across the application. The component improves
 * accessibility over the original Ant Design Tag by using semantic HTML buttons for interactive
 * elements like close and add actions, and includes proper ARIA labels.
 *
 * Custom props:
 * @param {BrandColor | string} [color] - Color of the tag. Use a Fides brand color whenever possible. Import CUSTOM_TAG_COLOR from fidesui to use a Fides brand color programmatically.
 * @param {boolean} [addable] - Shows an add icon at the end of the tag
 * @param {boolean} [hasSparkle] - Shows a sparkle icon before the content
 * @param {string} [closeButtonLabel="Remove"] - Aria label for the close button
 * @param {() => void} [onClick] - Makes the entire tag clickable by wrapping it in a button
 *
 * @examples
 * ```tsx
 * // Basic usage with brand colors
 * <Tag color="minos">Dark background</Tag>
 * <Tag color="marble">Light background</Tag>
 *
 * // Interactive tags
 * <Tag closable onClose={() => {}} closeButtonLabel="Remove item">Closable</Tag>
 * <Tag addable onClick={() => {}}>Add more</Tag>
 *
 * // With icons
 * <Tag hasSparkle>AI Generated</Tag>
 * <Tag><Icons.Edit />Editable</Tag>
 *
 * // Using a Fides brand color programmatically
 * const tagColor = CUSTOM_TAG_COLOR.MINOS;
 * <Tag color={tagColor}>Dark background</Tag>
 * ```
 */
export const CustomTag = withCustomProps(Tag);
