/**
 * Palette color constants — single source of truth for FidesUI brand colors.
 *
 * These values feed Ant Design's ThemeConfig (see ant-theme/default-theme.ts);
 * Ant's cssVar token system emits them as `--ant-brand-*` and `--ant-neutral-*`
 * CSS variables for use in component styles.
 */
export const palette = {
  // General
  FIDESUI_FULL_BLACK: "#000000",
  FIDESUI_FULL_WHITE: "#ffffff",
  FIDESUI_BG_WHITE: "#ffffff",

  // Neutral
  FIDESUI_NEUTRAL_50: "#fafafa",
  FIDESUI_NEUTRAL_75: "#f5f5f5",
  FIDESUI_NEUTRAL_100: "#e6e6e8",
  FIDESUI_NEUTRAL_200: "#d1d2d4",
  FIDESUI_NEUTRAL_300: "#bcbec1",
  FIDESUI_NEUTRAL_400: "#a8aaad",
  FIDESUI_NEUTRAL_500: "#93969a",
  FIDESUI_NEUTRAL_600: "#7e8185",
  FIDESUI_NEUTRAL_700: "#696c71",
  FIDESUI_NEUTRAL_800: "#53575c",
  FIDESUI_NEUTRAL_900: "#2b2e35",

  // Brand
  FIDESUI_BG_DEFAULT: "#f5f5f5",
  FIDESUI_CORINTH: "#fafafa",
  FIDESUI_BG_CORINTH: "#fafafa",
  FIDESUI_LIMESTONE: "#f1efee",
  FIDESUI_MINOS: "#2b2e35",
  FIDESUI_BG_MINOS: "#4f525b",
  FIDESUI_TERRACOTTA: "#b9704b",
  FIDESUI_BG_TERRACOTTA: "#f1b193",
  FIDESUI_OLIVE: "#999b83",
  FIDESUI_BG_OLIVE: "#d4d5c8",
  FIDESUI_MARBLE: "#cdd2d3",
  FIDESUI_BG_MARBLE: "#e1e5e6",
  FIDESUI_SANDSTONE: "#cecac2",
  FIDESUI_BG_SANDSTONE: "#e3e0d9",
  FIDESUI_NECTAR: "#f0ebc1",
  FIDESUI_BG_NECTAR: "#f5f2d7",

  // Functional
  FIDESUI_ERROR: "#d9534f",
  FIDESUI_BG_ERROR: "#f7c2c2",
  FIDESUI_WARNING: "#e59d47",
  FIDESUI_BG_WARNING: "#fbddb5",
  FIDESUI_BG_CAUTION: "#f6e3a4",
  FIDESUI_SUCCESS: "#5a9a68",
  FIDESUI_BG_SUCCESS: "#c3e6b2",
  FIDESUI_INFO: "#4a90e2",
  FIDESUI_BG_INFO: "#a5d6f3",
  FIDESUI_ALERT: "#7b4ea9",
  FIDESUI_BG_ALERT: "#d9b0d7",

  // Type
  FIDESUI_ERROR_TEXT: "#d32f2f",
  FIDESUI_SUCCESS_TEXT: "#388e3c",
  FIDESUI_LINK: "#2272ce",
} as const;
