import type { CSSProperties } from "react";

// ─── Responsive value types ───────────────────────────────────────────────────

type Breakpoint = "base" | "sm" | "md" | "lg" | "xl" | "2xl";
type ResponsiveObject<T> = Partial<Record<Breakpoint, T>>;

/**
 * Mirrors Chakra's `ResponsiveValue<T>`:
 *   - scalar           → applied at all breakpoints
 *   - array            → [base, sm, md, lg, xl, 2xl] (null skips that breakpoint)
 *   - breakpoint obj   → { base?, sm?, md?, lg?, xl?, "2xl"? }
 *
 * NOTE: Tailwind breakpoints differ slightly from Chakra's (sm: 640px vs 480px,
 * lg: 1024px vs 992px). This is acceptable for the transition shim.
 */
export type ResponsiveValue<T> =
  | T
  | null
  | Array<T | null | undefined>
  | ResponsiveObject<T>;

// ─── Types ────────────────────────────────────────────────────────────────────

export type SpacingValue = number | string;

// Widen spacing to accept responsive arrays that callers may already be passing
type RSpacing = ResponsiveValue<SpacingValue>;

/**
 * A subset of Chakra UI style props, accepted by the layout wrapper components
 * as a migration shim. Numeric spacing values use Chakra's scale (1 unit =
 * 0.25 rem, identical to Tailwind). String values are passed through as-is.
 *
 * NOTE: Chakra color tokens (e.g. "gray.200") are forwarded to inline styles
 * as-is and will not render correctly — replace them with Tailwind classes or
 * CSS values during per-file migration.
 */
export interface StyleProps {
  // Margin (shorthand + longhand + Chakra shorthands)
  m?: RSpacing;
  margin?: RSpacing;
  mt?: RSpacing;
  marginTop?: RSpacing;
  mb?: RSpacing;
  marginBottom?: RSpacing;
  ml?: RSpacing;
  marginLeft?: RSpacing;
  mr?: RSpacing;
  marginRight?: RSpacing;
  mx?: RSpacing;
  my?: RSpacing;
  /** Chakra alias for my */
  marginY?: RSpacing;
  // Padding (shorthand + longhand + Chakra shorthands)
  p?: RSpacing;
  padding?: RSpacing;
  pt?: RSpacing;
  paddingTop?: RSpacing;
  pb?: RSpacing;
  paddingBottom?: RSpacing;
  pl?: RSpacing;
  paddingLeft?: RSpacing;
  pr?: RSpacing;
  paddingRight?: RSpacing;
  px?: RSpacing;
  py?: RSpacing;
  paddingInline?: RSpacing;
  // Gap / spacing
  gap?: RSpacing;
  rowGap?: RSpacing;
  columnGap?: RSpacing;
  /** @deprecated CSS grid alias, use columnGap */
  gridColumnGap?: RSpacing;
  /** @deprecated CSS grid alias, use rowGap */
  gridRowGap?: RSpacing;
  /** Chakra Stack/VStack/HStack spacing prop — maps to CSS gap */
  spacing?: RSpacing;
  // Sizing
  w?: RSpacing;
  h?: RSpacing;
  width?: RSpacing;
  height?: RSpacing;
  minW?: RSpacing;
  maxW?: RSpacing;
  minH?: RSpacing;
  maxH?: RSpacing;
  minWidth?: RSpacing;
  maxWidth?: RSpacing;
  minHeight?: RSpacing;
  maxHeight?: RSpacing;
  /** Chakra shorthand — sets both width and height */
  boxSize?: RSpacing;
  // Flex layout
  direction?: ResponsiveValue<
    "row" | "column" | "row-reverse" | "column-reverse"
  >;
  flexDirection?: ResponsiveValue<CSSProperties["flexDirection"]>;
  /** Chakra alias for flexDirection */
  flexDir?: ResponsiveValue<CSSProperties["flexDirection"]>;
  /** Chakra alias for alignItems */
  align?: ResponsiveValue<CSSProperties["alignItems"]>;
  alignItems?: ResponsiveValue<CSSProperties["alignItems"]>;
  alignSelf?: ResponsiveValue<CSSProperties["alignSelf"]>;
  justifySelf?: ResponsiveValue<CSSProperties["justifySelf"]>;
  /** Chakra alias for justifyContent */
  justify?: ResponsiveValue<CSSProperties["justifyContent"]>;
  justifyContent?: ResponsiveValue<CSSProperties["justifyContent"]>;
  flex?: ResponsiveValue<number | string>;
  flexGrow?: ResponsiveValue<number | string>;
  /** Chakra alias for flexGrow */
  grow?: number;
  flexShrink?: ResponsiveValue<number | string>;
  flexBasis?: RSpacing;
  flexWrap?: ResponsiveValue<CSSProperties["flexWrap"]>;
  /** Chakra alias for flexWrap (used on HStack/Stack) */
  wrap?: ResponsiveValue<CSSProperties["flexWrap"]>;
  // Display / position / overflow
  display?: ResponsiveValue<CSSProperties["display"]>;
  position?: ResponsiveValue<CSSProperties["position"]>;
  top?: RSpacing;
  bottom?: RSpacing;
  left?: RSpacing;
  right?: RSpacing;
  overflow?: ResponsiveValue<CSSProperties["overflow"]>;
  overflowX?: ResponsiveValue<CSSProperties["overflowX"]>;
  overflowY?: ResponsiveValue<CSSProperties["overflowY"]>;
  zIndex?: ResponsiveValue<number | string>;
  visibility?: CSSProperties["visibility"];
  // Border
  border?: string;
  borderTop?: string;
  borderBottom?: string;
  borderLeft?: string;
  borderRight?: string;
  /** Chakra shorthand — sets borderTop + borderBottom */
  borderY?: string;
  borderWidth?: RSpacing;
  borderBottomWidth?: RSpacing;
  borderStyle?: string;
  borderColor?: string;
  borderRadius?: RSpacing;
  /** Chakra shorthand — sets borderTopLeftRadius + borderTopRightRadius */
  borderTopRadius?: RSpacing;
  /** Chakra shorthand — sets borderBottomLeftRadius + borderBottomRightRadius */
  borderBottomRadius?: RSpacing;
  // Background / color
  bg?: string;
  background?: string;
  backgroundColor?: string;
  /** Chakra alias for backgroundColor */
  bgColor?: string;
  color?: string;
  // Typography
  textAlign?: ResponsiveValue<CSSProperties["textAlign"]>;
  fontWeight?: string | number;
  fontSize?: string | number;
  lineHeight?: string | number;
  whiteSpace?: CSSProperties["whiteSpace"];
  textOverflow?: CSSProperties["textOverflow"];
  // Grid
  gridTemplateColumns?: string;
  // Misc
  cursor?: ResponsiveValue<CSSProperties["cursor"]>;
  pointerEvents?: CSSProperties["pointerEvents"];
  opacity?: number;
  boxShadow?: string;
  boxSizing?: CSSProperties["boxSizing"];
  userSelect?: CSSProperties["userSelect"];
}

// ─── Tailwind class lookup tables ─────────────────────────────────────────────

const FLEX_DIR: Record<string, string> = {
  row: "flex-row",
  column: "flex-col",
  "row-reverse": "flex-row-reverse",
  "column-reverse": "flex-col-reverse",
};

const ALIGN_ITEMS: Record<string, string> = {
  center: "items-center",
  "flex-start": "items-start",
  start: "items-start",
  "flex-end": "items-end",
  end: "items-end",
  stretch: "items-stretch",
  baseline: "items-baseline",
  normal: "items-normal",
};

const JUSTIFY_CONTENT: Record<string, string> = {
  center: "justify-center",
  "flex-start": "justify-start",
  start: "justify-start",
  "flex-end": "justify-end",
  end: "justify-end",
  "space-between": "justify-between",
  "space-around": "justify-around",
  "space-evenly": "justify-evenly",
  normal: "justify-normal",
  stretch: "justify-stretch",
};

const OVERFLOW_MAIN: Record<string, string> = {
  auto: "overflow-auto",
  hidden: "overflow-hidden",
  visible: "overflow-visible",
  scroll: "overflow-scroll",
};

const OVERFLOW_X: Record<string, string> = {
  auto: "overflow-x-auto",
  hidden: "overflow-x-hidden",
  visible: "overflow-x-visible",
  scroll: "overflow-x-scroll",
};

const OVERFLOW_Y: Record<string, string> = {
  auto: "overflow-y-auto",
  hidden: "overflow-y-hidden",
  visible: "overflow-y-visible",
  scroll: "overflow-y-scroll",
};

const POSITION_MAP: Record<string, string> = {
  relative: "relative",
  absolute: "absolute",
  fixed: "fixed",
  sticky: "sticky",
  static: "static",
};

const DISPLAY_MAP: Record<string, string> = {
  flex: "flex",
  "inline-flex": "inline-flex",
  block: "block",
  "inline-block": "inline-block",
  inline: "inline",
  none: "hidden",
  contents: "contents",
  grid: "grid",
  "inline-grid": "inline-grid",
  "flow-root": "flow-root",
};

const CURSOR_MAP: Record<string, string> = {
  auto: "cursor-auto",
  default: "cursor-default",
  pointer: "cursor-pointer",
  wait: "cursor-wait",
  text: "cursor-text",
  move: "cursor-move",
  "not-allowed": "cursor-not-allowed",
  crosshair: "cursor-crosshair",
  grab: "cursor-grab",
  grabbing: "cursor-grabbing",
};

const TEXT_ALIGN_MAP: Record<string, string> = {
  left: "text-left",
  center: "text-center",
  right: "text-right",
  justify: "text-justify",
  start: "text-start",
  end: "text-end",
};

const FLEX_WRAP_MAP: Record<string, string> = {
  wrap: "flex-wrap",
  nowrap: "flex-nowrap",
  "wrap-reverse": "flex-wrap-reverse",
};

/** Chakra borderRadius token → CSS value */
const BORDER_RADIUS_TOKENS: Record<string, string> = {
  none: "0",
  sm: "0.125rem",
  base: "0.25rem",
  md: "0.375rem",
  lg: "0.5rem",
  xl: "0.75rem",
  "2xl": "1rem",
  "3xl": "1.5rem",
  full: "9999px",
};

// ─── All style prop keys (used to partition props from HTML attrs) ─────────────

export const STYLE_PROP_KEYS = new Set<string>([
  "m",
  "margin",
  "mt",
  "marginTop",
  "mb",
  "marginBottom",
  "ml",
  "marginLeft",
  "mr",
  "marginRight",
  "mx",
  "my",
  "marginY",
  "p",
  "padding",
  "pt",
  "paddingTop",
  "pb",
  "paddingBottom",
  "pl",
  "paddingLeft",
  "pr",
  "paddingRight",
  "px",
  "py",
  "paddingInline",
  "gap",
  "rowGap",
  "columnGap",
  "gridColumnGap",
  "gridRowGap",
  "spacing",
  "w",
  "h",
  "width",
  "height",
  "minW",
  "maxW",
  "minH",
  "maxH",
  "minWidth",
  "maxWidth",
  "minHeight",
  "maxHeight",
  "boxSize",
  "direction",
  "flexDirection",
  "flexDir",
  "align",
  "alignItems",
  "alignSelf",
  "justify",
  "justifyContent",
  "justifySelf",
  "flex",
  "flexGrow",
  "grow",
  "flexShrink",
  "flexBasis",
  "flexWrap",
  "wrap",
  "display",
  "position",
  "visibility",
  "top",
  "bottom",
  "left",
  "right",
  "overflow",
  "overflowX",
  "overflowY",
  "zIndex",
  "border",
  "borderTop",
  "borderBottom",
  "borderLeft",
  "borderRight",
  "borderY",
  "borderWidth",
  "borderBottomWidth",
  "borderStyle",
  "borderColor",
  "borderRadius",
  "borderTopRadius",
  "borderBottomRadius",
  "bg",
  "background",
  "backgroundColor",
  "bgColor",
  "color",
  "textAlign",
  "fontWeight",
  "fontSize",
  "lineHeight",
  "whiteSpace",
  "textOverflow",
  "gridTemplateColumns",
  "cursor",
  "pointerEvents",
  "opacity",
  "boxShadow",
  "boxSizing",
  "userSelect",
]);

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Converts a Chakra spacing scale value (number) or a CSS string to a CSS string. */
function toCSS(v: SpacingValue): string {
  return typeof v === "number" ? `${v * 0.25}rem` : v;
}

const BREAKPOINT_PREFIXES = ["", "sm:", "md:", "lg:", "xl:", "2xl:"];
const BREAKPOINT_KEYS: Breakpoint[] = ["base", "sm", "md", "lg", "xl", "2xl"];

/**
 * Resolves a responsive enum value to one or more Tailwind classes.
 * String enums (direction, display, etc.) are looked up in the map;
 * unrecognised values fall back to inline style (handled by caller).
 */
function resolveEnum(
  map: Record<string, string>,
  value: ResponsiveValue<string> | undefined,
): string[] {
  if (value == null) {
    return [];
  }
  if (typeof value === "string") {
    const cls = map[value];
    return cls ? [cls] : [];
  }
  if (Array.isArray(value)) {
    return value.flatMap((v, i) => {
      if (v == null) {
        return [];
      }
      const cls = map[v as string];
      if (!cls) {
        return [];
      }
      return [i === 0 ? cls : `${BREAKPOINT_PREFIXES[i]}${cls}`];
    });
  }
  // Object form
  return BREAKPOINT_KEYS.flatMap((bp) => {
    const v = (value as ResponsiveObject<string>)[bp];
    if (v == null) {
      return [];
    }
    const cls = map[v as string];
    if (!cls) {
      return [];
    }
    return [bp === "base" ? cls : `${bp}:${cls}`];
  });
}

/**
 * Extracts the base (non-responsive) spacing value from a ResponsiveValue.
 * Only the base breakpoint is applied as an inline style; responsive spacing
 * must be migrated to Tailwind className at the call site.
 */
function baseOf(v: RSpacing | undefined): SpacingValue | undefined {
  if (v == null) {
    return undefined;
  }
  if (Array.isArray(v)) {
    return (v[0] as SpacingValue | null | undefined) ?? undefined;
  }
  if (typeof v === "object") {
    return (v as ResponsiveObject<SpacingValue>).base;
  }
  return v;
}

/** Like baseOf but for arbitrary responsive CSS values (e.g. alignSelf, justifySelf). */
function baseOfGeneric<T>(v: ResponsiveValue<T> | undefined): T | undefined {
  if (v == null) {
    return undefined;
  }
  if (Array.isArray(v)) {
    return (v[0] as T | null | undefined) ?? undefined;
  }
  if (typeof v === "object") {
    return (v as ResponsiveObject<T>).base;
  }
  return v as T;
}

// ─── Main converter ───────────────────────────────────────────────────────────

export interface ExtractedStyleProps {
  className: string;
  style: CSSProperties;
}

/**
 * Converts Chakra-compatible style props into `{ className, style }`.
 * String enum props (direction, alignItems, etc.) become Tailwind classes,
 * including responsive variants (e.g. `direction={["column","row"]}` →
 * `"flex-col sm:flex-row"`).
 * Numeric/arbitrary props (spacing, colors, borders, etc.) become inline styles
 * using the base breakpoint value only.
 * Returns the remainder as `rest` for spreading onto the DOM element.
 */
export function extractStyleProps<T extends StyleProps>(
  props: T,
): ExtractedStyleProps & { rest: Omit<T, keyof StyleProps> } {
  const classes: string[] = [];
  const style: CSSProperties = {};

  // ── Flex direction (direction / flexDir / flexDirection) ──
  const flexDirVal = props.direction ?? props.flexDir ?? props.flexDirection;
  if (flexDirVal !== undefined) {
    const resolved = resolveEnum(
      FLEX_DIR,
      flexDirVal as ResponsiveValue<string>,
    );
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof flexDirVal === "string") {
      style.flexDirection = flexDirVal as CSSProperties["flexDirection"];
    }
  }

  // ── Align items ──
  const ai = props.align ?? props.alignItems;
  if (ai !== undefined) {
    const resolved = resolveEnum(ALIGN_ITEMS, ai as ResponsiveValue<string>);
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof ai === "string") {
      style.alignItems = ai;
    }
  }

  // ── Justify content ──
  const jc = props.justify ?? props.justifyContent;
  if (jc !== undefined) {
    const resolved = resolveEnum(
      JUSTIFY_CONTENT,
      jc as ResponsiveValue<string>,
    );
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof jc === "string") {
      style.justifyContent = jc;
    }
  }

  // ── Flex wrap ──
  const fw = props.flexWrap ?? props.wrap;
  if (fw !== undefined) {
    const resolved = resolveEnum(FLEX_WRAP_MAP, fw as ResponsiveValue<string>);
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof fw === "string") {
      style.flexWrap = fw as CSSProperties["flexWrap"];
    }
  }

  // ── Display ──
  if (props.display !== undefined) {
    const resolved = resolveEnum(
      DISPLAY_MAP,
      props.display as ResponsiveValue<string>,
    );
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof props.display === "string") {
      style.display = props.display;
    }
  }

  // ── Position ──
  if (props.position !== undefined) {
    const resolved = resolveEnum(
      POSITION_MAP,
      props.position as ResponsiveValue<string>,
    );
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof props.position === "string") {
      style.position = props.position;
    }
  }

  // ── Overflow ──
  if (props.overflow !== undefined) {
    const resolved = resolveEnum(
      OVERFLOW_MAIN,
      props.overflow as ResponsiveValue<string>,
    );
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof props.overflow === "string") {
      style.overflow = props.overflow;
    }
  }
  if (props.overflowX !== undefined) {
    const resolved = resolveEnum(
      OVERFLOW_X,
      props.overflowX as ResponsiveValue<string>,
    );
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof props.overflowX === "string") {
      style.overflowX = props.overflowX;
    }
  }
  if (props.overflowY !== undefined) {
    const resolved = resolveEnum(
      OVERFLOW_Y,
      props.overflowY as ResponsiveValue<string>,
    );
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof props.overflowY === "string") {
      style.overflowY = props.overflowY;
    }
  }

  // ── Cursor ──
  if (props.cursor !== undefined) {
    const resolved = resolveEnum(
      CURSOR_MAP,
      props.cursor as ResponsiveValue<string>,
    );
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof props.cursor === "string") {
      style.cursor = props.cursor;
    }
  }

  // ── Text align ──
  if (props.textAlign !== undefined) {
    const resolved = resolveEnum(
      TEXT_ALIGN_MAP,
      props.textAlign as ResponsiveValue<string>,
    );
    if (resolved.length > 0) {
      classes.push(...resolved);
    } else if (typeof props.textAlign === "string") {
      style.textAlign = props.textAlign;
    }
  }

  // ── Inline style props ────────────────────────────────────────────────────

  // Margin
  const margin = baseOf(props.m ?? props.margin);
  if (margin !== undefined) {
    style.margin = toCSS(margin);
  }
  const mt = baseOf(props.mt ?? props.marginTop);
  if (mt !== undefined) {
    style.marginTop = toCSS(mt);
  }
  const mb = baseOf(props.mb ?? props.marginBottom);
  if (mb !== undefined) {
    style.marginBottom = toCSS(mb);
  }
  const ml = baseOf(props.ml ?? props.marginLeft);
  if (ml !== undefined) {
    style.marginLeft = toCSS(ml);
  }
  const mr = baseOf(props.mr ?? props.marginRight);
  if (mr !== undefined) {
    style.marginRight = toCSS(mr);
  }
  const mxVal = baseOf(props.mx);
  if (mxVal !== undefined) {
    style.marginLeft = toCSS(mxVal);
    style.marginRight = toCSS(mxVal);
  }
  const my = baseOf(props.my ?? props.marginY);
  if (my !== undefined) {
    style.marginTop = toCSS(my);
    style.marginBottom = toCSS(my);
  }

  // Padding
  const padding = baseOf(props.p ?? props.padding);
  if (padding !== undefined) {
    style.padding = toCSS(padding);
  }
  const pt = baseOf(props.pt ?? props.paddingTop);
  if (pt !== undefined) {
    style.paddingTop = toCSS(pt);
  }
  const pb = baseOf(props.pb ?? props.paddingBottom);
  if (pb !== undefined) {
    style.paddingBottom = toCSS(pb);
  }
  const pl = baseOf(props.pl ?? props.paddingLeft);
  if (pl !== undefined) {
    style.paddingLeft = toCSS(pl);
  }
  const pr = baseOf(props.pr ?? props.paddingRight);
  if (pr !== undefined) {
    style.paddingRight = toCSS(pr);
  }
  const pxVal = baseOf(props.px);
  if (pxVal !== undefined) {
    style.paddingLeft = toCSS(pxVal);
    style.paddingRight = toCSS(pxVal);
  }
  const pyVal = baseOf(props.py);
  if (pyVal !== undefined) {
    style.paddingTop = toCSS(pyVal);
    style.paddingBottom = toCSS(pyVal);
  }
  const paddingInline = baseOf(props.paddingInline);
  if (paddingInline !== undefined) {
    style.paddingInline = toCSS(paddingInline);
  }

  // Gap
  const gapVal = baseOf(props.gap);
  if (gapVal !== undefined) {
    style.gap = toCSS(gapVal);
  }
  const rowGapVal = baseOf(props.rowGap ?? props.gridRowGap);
  if (rowGapVal !== undefined) {
    style.rowGap = toCSS(rowGapVal);
  }
  const colGap = baseOf(props.columnGap ?? props.gridColumnGap);
  if (colGap !== undefined) {
    style.columnGap = toCSS(colGap);
  }
  const spacingVal = baseOf(props.spacing);
  if (spacingVal !== undefined) {
    style.gap = toCSS(spacingVal);
  }

  // Sizing
  const w = baseOf(props.w ?? props.width);
  if (w !== undefined) {
    style.width = toCSS(w);
  }
  const h = baseOf(props.h ?? props.height);
  if (h !== undefined) {
    style.height = toCSS(h);
  }
  const boxSizeVal = baseOf(props.boxSize);
  if (boxSizeVal !== undefined) {
    style.width = toCSS(boxSizeVal);
    style.height = toCSS(boxSizeVal);
  }
  const minW = baseOf(props.minW ?? props.minWidth);
  if (minW !== undefined) {
    style.minWidth = toCSS(minW);
  }
  const maxW = baseOf(props.maxW ?? props.maxWidth);
  if (maxW !== undefined) {
    style.maxWidth = toCSS(maxW);
  }
  const minH = baseOf(props.minH ?? props.minHeight);
  if (minH !== undefined) {
    style.minHeight = toCSS(minH);
  }
  const maxH = baseOf(props.maxH ?? props.maxHeight);
  if (maxH !== undefined) {
    style.maxHeight = toCSS(maxH);
  }

  // Flex numeric/mixed props
  const flexVal = baseOfGeneric(props.flex);
  if (flexVal !== undefined) {
    style.flex = flexVal;
  }
  const flexGrow = baseOfGeneric(props.flexGrow) ?? props.grow;
  if (flexGrow !== undefined) {
    style.flexGrow =
      typeof flexGrow === "string" ? parseFloat(flexGrow) : flexGrow;
  }
  const flexShrink = baseOfGeneric(props.flexShrink);
  if (flexShrink !== undefined) {
    style.flexShrink =
      typeof flexShrink === "string" ? parseFloat(flexShrink) : flexShrink;
  }
  const flexBasisVal = baseOf(props.flexBasis);
  if (flexBasisVal !== undefined) {
    style.flexBasis = toCSS(flexBasisVal);
  }

  // align-self / justify-self
  const alignSelfVal = baseOfGeneric(props.alignSelf);
  if (alignSelfVal !== undefined) {
    style.alignSelf = alignSelfVal;
  }
  const justifySelfVal = baseOfGeneric(props.justifySelf);
  if (justifySelfVal !== undefined) {
    style.justifySelf = justifySelfVal;
  }

  // Position offsets
  const topVal = baseOf(props.top);
  if (topVal !== undefined) {
    style.top = toCSS(topVal);
  }
  const bottomVal = baseOf(props.bottom);
  if (bottomVal !== undefined) {
    style.bottom = toCSS(bottomVal);
  }
  const leftVal = baseOf(props.left);
  if (leftVal !== undefined) {
    style.left = toCSS(leftVal);
  }
  const rightVal = baseOf(props.right);
  if (rightVal !== undefined) {
    style.right = toCSS(rightVal);
  }

  // Z-index / visibility
  const zIndexVal = baseOfGeneric(props.zIndex);
  if (zIndexVal !== undefined) {
    style.zIndex = zIndexVal;
  }
  if (props.visibility !== undefined) {
    style.visibility = props.visibility;
  }
  // Border
  if (props.border !== undefined) {
    style.border = props.border;
  }
  if (props.borderTop !== undefined) {
    style.borderTop = props.borderTop;
  }
  if (props.borderBottom !== undefined) {
    style.borderBottom = props.borderBottom;
  }
  if (props.borderLeft !== undefined) {
    style.borderLeft = props.borderLeft;
  }
  if (props.borderRight !== undefined) {
    style.borderRight = props.borderRight;
  }
  if (props.borderY !== undefined) {
    style.borderTop = props.borderY;
    style.borderBottom = props.borderY;
  }
  const borderWidthVal = baseOf(props.borderWidth);
  if (borderWidthVal !== undefined) {
    style.borderWidth = toCSS(borderWidthVal);
  }
  const borderBottomWidthVal = baseOf(props.borderBottomWidth);
  if (borderBottomWidthVal !== undefined) {
    style.borderBottomWidth = toCSS(borderBottomWidthVal);
  }
  if (props.borderStyle !== undefined) {
    style.borderStyle = props.borderStyle;
  }
  if (props.borderColor !== undefined) {
    style.borderColor = props.borderColor;
  }
  const borderRadiusVal = baseOf(props.borderRadius);
  if (borderRadiusVal !== undefined) {
    style.borderRadius =
      typeof borderRadiusVal === "number"
        ? toCSS(borderRadiusVal)
        : (BORDER_RADIUS_TOKENS[borderRadiusVal] ?? borderRadiusVal);
  }
  const borderTopRadiusVal = baseOf(props.borderTopRadius);
  if (borderTopRadiusVal !== undefined) {
    const r =
      typeof borderTopRadiusVal === "number"
        ? toCSS(borderTopRadiusVal)
        : (BORDER_RADIUS_TOKENS[borderTopRadiusVal] ?? borderTopRadiusVal);
    style.borderTopLeftRadius = r;
    style.borderTopRightRadius = r;
  }
  const borderBottomRadiusVal = baseOf(props.borderBottomRadius);
  if (borderBottomRadiusVal !== undefined) {
    const r =
      typeof borderBottomRadiusVal === "number"
        ? toCSS(borderBottomRadiusVal)
        : (BORDER_RADIUS_TOKENS[borderBottomRadiusVal] ??
          borderBottomRadiusVal);
    style.borderBottomLeftRadius = r;
    style.borderBottomRightRadius = r;
  }

  // Background / color
  const bg =
    props.bg ?? props.background ?? props.backgroundColor ?? props.bgColor;
  if (bg !== undefined) {
    style.background = bg;
  }
  if (props.color !== undefined) {
    style.color = props.color;
  }

  // Typography
  if (props.fontWeight !== undefined) {
    style.fontWeight = props.fontWeight;
  }
  if (props.fontSize !== undefined) {
    style.fontSize = props.fontSize;
  }
  if (props.lineHeight !== undefined) {
    style.lineHeight = props.lineHeight;
  }
  if (props.whiteSpace !== undefined) {
    style.whiteSpace = props.whiteSpace;
  }
  if (props.textOverflow !== undefined) {
    style.textOverflow = props.textOverflow;
  }

  // Grid
  if (props.gridTemplateColumns !== undefined) {
    style.gridTemplateColumns = props.gridTemplateColumns;
  }

  // Misc
  if (props.pointerEvents !== undefined) {
    style.pointerEvents = props.pointerEvents;
  }
  if (props.opacity !== undefined) {
    style.opacity = props.opacity;
  }
  if (props.boxShadow !== undefined) {
    style.boxShadow = props.boxShadow;
  }
  if (props.boxSizing !== undefined) {
    style.boxSizing = props.boxSizing;
  }
  if (props.userSelect !== undefined) {
    style.userSelect = props.userSelect;
  }

  // ── Build rest (HTML props without style prop keys) ──────────────────────
  const rest = {} as Record<string, unknown>;
  Object.keys(props).forEach((key) => {
    if (!STYLE_PROP_KEYS.has(key)) {
      rest[key] = (props as Record<string, unknown>)[key];
    }
  });

  return {
    className: classes.filter(Boolean).join(" "),
    style,
    rest: rest as Omit<T, keyof StyleProps>,
  };
}
