import React from "react";

import { extractStyleProps, StyleProps } from "./styleProps";

export type FlexProps = StyleProps & {
  as?: React.ElementType;
} & Omit<React.HTMLAttributes<HTMLElement>, keyof StyleProps | "color">;

export const Flex = React.forwardRef<HTMLElement, FlexProps>(
  ({ as: Component = "div", className, style, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <Component
        ref={ref}
        className={["flex", twClassName, className].filter(Boolean).join(" ")}
        style={{ ...twStyle, ...style }}
        {...rest}
      />
    );
  },
);
Flex.displayName = "Flex";
