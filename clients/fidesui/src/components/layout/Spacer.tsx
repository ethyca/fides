import React from "react";

import { extractStyleProps, StyleProps } from "./styleProps";

export type SpacerProps = StyleProps &
  Omit<React.HTMLAttributes<HTMLDivElement>, keyof StyleProps | "color">;

export const Spacer = React.forwardRef<HTMLDivElement, SpacerProps>(
  ({ className, style, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <div
        ref={ref}
        className={["flex-1", twClassName, className].filter(Boolean).join(" ")}
        style={{ ...twStyle, ...style }}
        {...rest}
      />
    );
  },
);
Spacer.displayName = "Spacer";
