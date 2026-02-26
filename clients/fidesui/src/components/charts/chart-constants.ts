import type { GlobalToken } from "antd";

export type AntColorTokenKey = Extract<keyof GlobalToken, `color${string}`>;

// Brand caption typography: Basier Square Mono, Regular, -3% letter spacing, 150% line height.
// fontFamily is sourced from token.fontFamilyCode (see default-theme.ts).
// lineHeight is documented for intent; SVG <text> elements require tspan dy offsets for multi-line use.
export const CHART_TYPOGRAPHY = {
  fontWeight: 400,
  letterSpacing: "-0.03em",
  lineHeight: 1.5,
} as const;

export const CHART_ANIMATION = {
  defaultDuration: 600,
  easing: "ease-in-out" as const,
} as const;

export const CHART_STROKE = {
  strokeWidth: 2,
  strokeOpacity: 0.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
} as const;

export const CHART_GRADIENT = {
  startOpacity: 0.25,
  endOpacity: 0,
} as const;

export const COLOR_OPTIONS = [
  undefined,
  "colorPrimary",
  "colorSuccess",
  "colorWarning",
  "colorError",
  "colorInfo",
  "colorText",
  "colorTextSecondary",
  "colorTextTertiary",
  "colorBorder",
] as const;
