import { generate } from "@ant-design/colors";
import { theme, ThemeConfig } from "antd";

import { palette } from "../palette/palette";
import { defaultAntTheme } from "./default-theme";

/**
 * Dark mode theme for Ant Design components.
 * Uses Ant Design's built-in darkAlgorithm for automatic dark color generation,
 * with custom overrides to match the Fides brand palette.
 * The generate function creates a 10-shade dark palette for a base color against the dark background.
 * Lower index returns a darker variant.
 * */
const dark = (color: string) =>
  generate(color, { theme: "dark", backgroundColor: palette.FIDESUI_BG_MINOS });

const minosDark = dark(palette.FIDESUI_MINOS);
const errorDark = dark(palette.FIDESUI_ERROR);
const warningDark = dark(palette.FIDESUI_WARNING);
const corinthDark = dark(palette.FIDESUI_CORINTH);

// Brand palette tokens (--fidesui-brand-minos, --fidesui-brand-corinth, etc.) are
// semantic anchors used as fixed accents/borders/surfaces across the codebase
// — they stay constant across themes. Theme-aware flipping happens via Ant's
// built-in tokens (colorText, colorBgBase, colorPrimary, etc.) below.

export const darkAntTheme: ThemeConfig = {
  ...defaultAntTheme,
  // Distinct cssVar key so antd emits a separate `.fidesui-dark` block we can
  // scope to dark-mode subtrees without colliding with the outer light block.
  cssVar: { ...defaultAntTheme.cssVar, key: "fidesui-dark" },
  algorithm: theme.darkAlgorithm,
  token: {
    ...defaultAntTheme.token,
    colorBgBase: palette.FIDESUI_BG_MINOS,
    colorTextBase: palette.FIDESUI_CORINTH,
    colorText: palette.FIDESUI_CORINTH,
    colorTextDescription: corinthDark[4],
    colorTextHeading: palette.FIDESUI_CORINTH,
    colorPrimary: palette.FIDESUI_CORINTH,
    colorBgContainer: palette.FIDESUI_BG_MINOS,
    colorBorder: minosDark[4],
    colorErrorBg: errorDark[1],
    colorErrorBorder: errorDark[3],
    colorWarningBg: warningDark[1],
    colorWarningBorder: warningDark[3],
  },
  components: {
    ...defaultAntTheme.components,
    Alert: {
      ...defaultAntTheme.components?.Alert,
      colorInfo: palette.FIDESUI_CORINTH,
      colorInfoBg: minosDark[1],
      colorInfoBorder: minosDark[3],
    },
    Button: {
      defaultBg: palette.FIDESUI_BG_MINOS,
    },
    Layout: {
      bodyBg: palette.FIDESUI_BG_MINOS,
    },
    Card: {
      colorBgContainer: palette.FIDESUI_MINOS,
    },
    Select: {
      ...defaultAntTheme.components?.Select,
      colorBgElevated: palette.FIDESUI_BG_MINOS,
      optionActiveBg: minosDark[2],
      optionSelectedBg: minosDark[3],
    },
  },
};
