import { Tooltip, TooltipProps } from "antd/lib";
import React, { ReactElement } from "react";

import styles from "./CustomTooltip.module.scss";

interface CustomTooltipProps extends Omit<TooltipProps, "children"> {
  children: ReactElement | string;
  tabIndex?: number;
}

/**
 * Higher-order component that adds keyboard accessibility support to Ant Design's Tooltip component.
 * Automatically adds tabindex, onFocus, and onBlur handlers to the child element to make tooltips
 * accessible via keyboard navigation. This only works when there's exactly one child element.
 */
const withCustomProps = (WrappedComponent: typeof Tooltip) => {
  const WrappedTooltip = ({ children, ...props }: CustomTooltipProps) => {
    let childElement: ReactElement;
    if (typeof children === "string") {
      // If children is a string, wrap it in a span to make it focusable
      childElement = <span>{children}</span>;
    } else if (!React.isValidElement(children)) {
      return <WrappedComponent {...props}>{children}</WrappedComponent>;
    } else {
      childElement = children;
    }

    const existingProps = childElement.props as CustomTooltipProps;
    const elementType = childElement.type as string;

    // Check if element is naturally focusable (button, anchor, input, etc.)
    const isNaturallyFocusable = [
      "button",
      "a",
      "input",
      "textarea",
      "select",
    ].includes(elementType);

    // Create enhanced props for keyboard accessibility
    const enhancedProps = {
      ...existingProps,
      // Only add tabIndex if element isn't naturally focusable and doesn't already have one
      tabIndex:
        existingProps.tabIndex ?? (isNaturallyFocusable ? undefined : 0),
      className:
        `${existingProps.className ?? ""} ${!isNaturallyFocusable ? styles.tooltipChild : ""}`.trim(),
    };

    // Clone the child element with enhanced props
    const enhancedChild = React.cloneElement(childElement, enhancedProps);

    return (
      <WrappedComponent {...props} trigger={["focus", "hover"]}>
        {enhancedChild}
      </WrappedComponent>
    );
  };

  return WrappedTooltip;
};

/**
 * CustomTooltip extends Ant Design's Tooltip component with keyboard accessibility support.
 * It automatically adds tabindex to the child element, and sets the trigger to "focus" and "hover".
 * allowing keyboard users to trigger tooltips by focusing on the element.
 *
 * Features:
 * - Automatically adds tabIndex={0} to non-focusable elements (skips buttons, anchors, inputs, etc.)
 * - Shows tooltip on focus and hover
 * - Only works with single child elements (React limitation for cloneElement)
 *
 * @example
 * ```tsx
 * // Basic usage with button (no tabIndex added - naturally focusable)
 * <Tooltip title="Helpful information">
 *   <button>Hover or focus me</button>
 * </Tooltip>
 *
 * // With non-focusable element (tabIndex={0} added automatically)
 * <Tooltip title="Status information">
 *   <span>Basic text</span>
 * </Tooltip>
 *
 * // With string (<span tabIndex={0} /> added automatically)
 * <Tooltip title="Status information">
 *   "Basic text"
 * </Tooltip>
 *
 * // With anchor tag (no tabIndex added - naturally focusable)
 * <Tooltip title="Link information">
 *   <a href="#example">Link text</a>
 * </Tooltip>
 *
 * // Override behavior with explicit tabIndex
 * <Tooltip title="Custom tab order">
 *   <div tabIndex={1}>Custom focus order</div>
 * </Tooltip>
 * ```
 */
export const CustomTooltip = withCustomProps(Tooltip);
