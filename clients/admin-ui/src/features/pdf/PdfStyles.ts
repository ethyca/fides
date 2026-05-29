import { StyleSheet } from "@react-pdf/renderer";
import { palette } from "fidesui/src/palette/palette";

export const HeaderStyles = StyleSheet.create({
  h1: {
    fontFamily: "Eliza",
    fontSize: 50,
  },
  h2: {
    fontFamily: "BasierSquare",
    fontSize: 40,
  },
  h3: {
    fontSize: 20,
    fontFamily: "Eliza",
  },
  h4: {
    fontSize: 15,
    fontFamily: "BasierSquare",
    textTransform: "uppercase",
    fontWeight: 600,
  },
  h5: {
    fontSize: 10,
    fontFamily: "BasierSquare",
  },
});

export const TextStyles = StyleSheet.create({
  small: {
    fontSize: 8,
  },
  medium: {
    fontSize: 10,
  },
  large: {
    fontSize: 12,
  },
  xl: {
    fontSize: 14,
  },
  bold: {
    fontSize: 50,
  },
  primary: {
    color: palette.FIDESUI_NEUTRAL_800,
  },
  secondary: {
    color: palette.FIDESUI_NEUTRAL_600,
  },
  highlight: {
    color: palette.FIDESUI_TERRACOTTA,
  },
});

export const VISUAL_COLORS = [
  palette.FIDESUI_MINOS,
  palette.FIDESUI_TERRACOTTA,
  palette.FIDESUI_OLIVE,
  palette.FIDESUI_NECTAR,
  palette.FIDESUI_MARBLE,
  palette.FIDESUI_CORINTH,
  palette.FIDESUI_BG_MINOS,
  palette.FIDESUI_BG_TERRACOTTA,
  palette.FIDESUI_BG_OLIVE,
  palette.FIDESUI_BG_NECTAR,
  palette.FIDESUI_BG_MARBLE,
  palette.FIDESUI_BG_SANDSTONE,
  palette.FIDESUI_LIMESTONE,
] as const;

export const VisualColorStyles = StyleSheet.create({
  v1: {
    color: palette.FIDESUI_NEUTRAL_800,
  },
  v2: {
    color: palette.FIDESUI_NEUTRAL_600,
  },
  v3: {
    color: palette.FIDESUI_TERRACOTTA,
  },
  v4: {
    color: palette.FIDESUI_NEUTRAL_800,
  },
  v5: {
    color: palette.FIDESUI_NEUTRAL_600,
  },
  v6: {
    color: palette.FIDESUI_TERRACOTTA,
  },
  v7: {
    color: palette.FIDESUI_NEUTRAL_800,
  },
  v8: {
    color: palette.FIDESUI_NEUTRAL_600,
  },
  v9: {
    color: palette.FIDESUI_TERRACOTTA,
  },
});
