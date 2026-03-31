import React from "react";

import { extractStyleProps, StyleProps } from "./styleProps";

export type CenterProps = StyleProps & {
  as?: React.ElementType;
} & Omit<React.HTMLAttributes<HTMLElement>, keyof StyleProps | "color">;

export const Center = React.forwardRef<HTMLElement, CenterProps>(
  ({ as: Component = "div", className, style, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <Component
        ref={ref}
        className={["flex items-center justify-center", twClassName, className]
          .filter(Boolean)
          .join(" ")}
        style={{ ...twStyle, ...style }}
        {...rest}
      />
    );
  },
);
Center.displayName = "Center";
