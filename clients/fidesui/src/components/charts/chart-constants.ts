import type { GlobalToken } from "antd";

export type AntColorTokenKey = Extract<keyof GlobalToken, `color${string}`>;

export const CHART_TYPOGRAPHY = {
  fontWeight: 400,
  letterSpacing: "-0.03em",
} as const;

export const CHART_ANIMATION = {
  defaultDuration: 600,
  easing: "ease-in-out" as const,
} as const;

export const CHART_STROKE = {
  strokeWidth: 2,
  strokeOpacity: 0.8,
  dotRadius: 3.5,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
} as const;

export const CHART_GRADIENT = {
  startOpacity: 0.25,
  endOpacity: 0,
} as const;

export const DONUT_THICKNESS = {
  default: 8,
  thick: 16,
} as const;

export type BarSize = "sm" | "md" | "lg";

export type AntSizeTokenKey = Extract<keyof GlobalToken, `size${string}`>;

export const BAR_SIZE_TOKEN: Record<BarSize, AntSizeTokenKey> = {
  sm: "sizeXS",
  md: "sizeSM",
  lg: "sizeLG",
} as const;

export const LABEL_WIDTH = 110;

export const MIN_PX_PER_POINT = 12;

export const COLOR_OPTIONS = [
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
