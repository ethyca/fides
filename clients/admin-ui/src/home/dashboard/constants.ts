import palette from "fidesui/src/palette/palette.module.scss";

/**
 * Color mappings for field statuses
 */
export const FIELD_STATUS_COLORS = {
  unlabeled: palette.FIDESUI_NEUTRAL_400,
  inReview: palette.FIDESUI_WARNING,
  approved: palette.FIDESUI_SUCCESS,
  confirmed: palette.FIDESUI_INFO,
} as const;

/**
 * Color array for treemap (as fallback)
 */
export const TREEMAP_COLORS = [
  palette.FIDESUI_INFO,
  palette.FIDESUI_SUCCESS,
  palette.FIDESUI_WARNING,
  palette.FIDESUI_TERRACOTTA,
  palette.FIDESUI_OLIVE,
  palette.FIDESUI_SANDSTONE,
  palette.FIDESUI_MARBLE,
  palette.FIDESUI_NECTAR,
] as const;

/**
 * Chart configuration constants
 */
export const CHART_CONFIG = {
  pieChart: {
    outerRadius: 100,
    labelFontSize: 12,
  },
  lineChart: {
    strokeWidth: 2,
    fontSize: 12,
  },
  treemap: {
    defaultHeight: 400,
    minWidth: 800,
    minHeight: 400,
  },
} as const;

