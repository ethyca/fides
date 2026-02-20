import { theme, ThemeConfig } from "antd";

import palette from "../palette/palette.module.scss";
import { defaultAntTheme } from "./default-theme";

/**
 * Dark mode theme for Ant Design components.
 * Uses Ant Design's built-in darkAlgorithm for automatic dark color generation,
 * with custom overrides to match the Fides brand palette.
 */
export const darkAntTheme: ThemeConfig = {
  ...defaultAntTheme,
  algorithm: theme.darkAlgorithm,
  cssVar: true,
  token: {
    ...defaultAntTheme.token,
    colorBgBase: palette.FIDESUI_BG_MINOS,
    colorTextBase: palette.FIDESUI_CORINTH,
    colorText: palette.FIDESUI_CORINTH,
    colorTextHeading: palette.FIDESUI_CORINTH,
    colorPrimary: palette.FIDESUI_CORINTH,
    colorBgContainer: palette.FIDESUI_BG_MINOS,
    colorBorder: "#3a3a3a",
  },
  components: {
    ...defaultAntTheme.components,
    Layout: {
      bodyBg: palette.FIDESUI_BG_MINOS,
    },
  },
};
