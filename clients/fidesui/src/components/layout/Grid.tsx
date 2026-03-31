import React from "react";

import { extractStyleProps, ResponsiveValue, StyleProps } from "./styleProps";

function baseColumns(
  v: ResponsiveValue<number | string> | undefined,
): number | string | undefined {
  if (v == null) {
    return undefined;
  }
  if (Array.isArray(v)) {
    return (v[0] as number | string | null | undefined) ?? undefined;
  }
  if (typeof v === "object") {
    return (v as Partial<Record<string, number | string>>).base;
  }
  return v;
}

// ── Grid ───────────────────────────────────────────────────────────────────────

export type GridProps = StyleProps & {
  as?: React.ElementType;
  /** CSS grid-template-columns value */
  templateColumns?: string;
  /** CSS grid-template-rows value */
  templateRows?: string;
} & Omit<React.HTMLAttributes<HTMLElement>, keyof StyleProps | "color">;

export const Grid = React.forwardRef<HTMLElement, GridProps>(
  (
    {
      as: Component = "div",
      className,
      style,
      templateColumns,
      templateRows,
      ...props
    },
    ref,
  ) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);
    return (
      <Component
        ref={ref}
        className={["grid", twClassName, className].filter(Boolean).join(" ")}
        style={{
          ...twStyle,
          ...(templateColumns ? { gridTemplateColumns: templateColumns } : {}),
          ...(templateRows ? { gridTemplateRows: templateRows } : {}),
          ...style,
        }}
        {...rest}
      />
    );
  },
);
Grid.displayName = "Grid";

// ── SimpleGrid ─────────────────────────────────────────────────────────────────

export type SimpleGridProps = StyleProps & {
  as?: React.ElementType;
  /**
   * Number of columns. Accepts a number, a responsive object/array (base
   * breakpoint value is applied), or a CSS grid-template-columns string.
   */
  columns?: ResponsiveValue<number | string>;
} & Omit<React.HTMLAttributes<HTMLElement>, keyof StyleProps | "color">;

export const SimpleGrid = React.forwardRef<HTMLElement, SimpleGridProps>(
  ({ as: Component = "div", className, style, columns, ...props }, ref) => {
    const {
      className: twClassName,
      style: twStyle,
      rest,
    } = extractStyleProps(props);

    const colBase = baseColumns(columns);
    let gridTemplateColumns: string | undefined;
    if (colBase !== undefined) {
      gridTemplateColumns =
        typeof colBase === "number"
          ? `repeat(${colBase}, minmax(0, 1fr))`
          : colBase;
    }

    return (
      <Component
        ref={ref}
        className={["grid", twClassName, className].filter(Boolean).join(" ")}
        style={{
          ...twStyle,
          ...(gridTemplateColumns ? { gridTemplateColumns } : {}),
          ...style,
        }}
        {...rest}
      />
    );
  },
);
SimpleGrid.displayName = "SimpleGrid";
