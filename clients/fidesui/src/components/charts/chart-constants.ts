import type { GlobalToken } from "antd";

export type AntColorTokenKey = Extract<keyof GlobalToken, `color${string}`>;

export const CHART_ANIMATION = {
  defaultDuration: 600,
  easing: "ease-in-out" as const,
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
