import React from "react";

import { extractStyleProps, StyleProps } from "./styleProps";

export type ContainerProps = StyleProps & {
  as?: React.ElementType;
} & Omit<React.HTMLAttributes<HTMLElement>, keyof StyleProps | "color">;

export const Container = React.forwardRef<HTMLElement, ContainerProps>(
  ({ as: Component = "div", className, style, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <Component
        ref={ref}
        className={["container mx-auto", twClassName, className]
          .filter(Boolean)
          .join(" ")}
        style={{ ...twStyle, ...style }}
        {...rest}
      />
    );
  },
);
Container.displayName = "Container";
