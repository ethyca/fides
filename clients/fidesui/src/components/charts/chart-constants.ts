import type { GlobalToken } from "antd";

export type AntColorTokenKey = Extract<keyof GlobalToken, `color${string}`>;

export const CHART_TYPOGRAPHY = {
  fontWeight: 400,
  letterSpacing: "-0.03em",
} as const;
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
