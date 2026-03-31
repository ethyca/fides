import React from "react";

import { extractStyleProps, StyleProps } from "./styleProps";

export type WrapProps = StyleProps & {
  as?: React.ElementType;
} & Omit<React.HTMLAttributes<HTMLElement>, keyof StyleProps | "color">;

export const Wrap = React.forwardRef<HTMLElement, WrapProps>(
  ({ as: Component = "div", className, style, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <Component
        ref={ref}
        className={["flex flex-wrap", twClassName, className]
          .filter(Boolean)
          .join(" ")}
        style={{ ...twStyle, ...style }}
        {...rest}
      />
    );
  },
);
Wrap.displayName = "Wrap";
