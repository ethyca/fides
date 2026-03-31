import React from "react";

import { extractStyleProps, StyleProps } from "./styleProps";

type StackBaseProps = StyleProps & {
  as?: React.ElementType;
} & Omit<React.HTMLAttributes<HTMLElement>, keyof StyleProps | "color">;

// ── Stack ──────────────────────────────────────────────────────────────────────

export type StackProps = StackBaseProps;

export const Stack = React.forwardRef<HTMLElement, StackProps>(
  ({ as: Component = "div", className, style, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <Component
        ref={ref}
        className={["flex flex-col", twClassName, className]
          .filter(Boolean)
          .join(" ")}
        style={{ ...twStyle, ...style }}
        {...rest}
      />
    );
  },
);
Stack.displayName = "Stack";

// ── VStack ─────────────────────────────────────────────────────────────────────

export type VStackProps = StackBaseProps;

export const VStack = React.forwardRef<HTMLElement, VStackProps>(
  ({ as: Component = "div", className, style, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <Component
        ref={ref}
        className={["flex flex-col items-center", twClassName, className]
          .filter(Boolean)
          .join(" ")}
        style={{ ...twStyle, ...style }}
        {...rest}
      />
    );
  },
);
VStack.displayName = "VStack";

// ── HStack ─────────────────────────────────────────────────────────────────────

export type HStackProps = StackBaseProps;

export const HStack = React.forwardRef<HTMLElement, HStackProps>(
  ({ as: Component = "div", className, style, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <Component
        ref={ref}
        className={["flex flex-row items-center", twClassName, className]
          .filter(Boolean)
          .join(" ")}
        style={{ ...twStyle, ...style }}
        {...rest}
      />
    );
  },
);
HStack.displayName = "HStack";
