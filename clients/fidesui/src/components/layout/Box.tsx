import React from "react";

import { extractStyleProps, StyleProps } from "./styleProps";

export type BoxProps = StyleProps & {
  as?: React.ElementType;
} & Omit<React.HTMLAttributes<HTMLElement>, keyof StyleProps | "color">;

export const Box = React.forwardRef<HTMLElement, BoxProps>(
  ({ as: Component = "div", className, style, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <Component
        ref={ref}
        className={[twClassName, className].filter(Boolean).join(" ")}
        style={{ ...twStyle, ...style }}
        {...rest}
      />
    );
  },
);
Box.displayName = "Box";
