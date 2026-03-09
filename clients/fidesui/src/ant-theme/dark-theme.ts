import { generate } from "@ant-design/colors";
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
    Alert: {
      colorInfoBg: generate(palette.FIDESUI_NEUTRAL_500, {
        theme: "dark",
        backgroundColor: palette.FIDESUI_BG_MINOS,
      })[0],
      colorInfo: generate(palette.FIDESUI_NEUTRAL_500, {
        theme: "dark",
        backgroundColor: palette.FIDESUI_BG_MINOS,
      })[4],
      colorWarningBg: generate(palette.FIDESUI_WARNING, {
        theme: "dark",
        backgroundColor: palette.FIDESUI_BG_MINOS,
      })[0],
      colorWarning: generate(palette.FIDESUI_WARNING, {
        theme: "dark",
        backgroundColor: palette.FIDESUI_BG_MINOS,
      })[4],
      colorErrorBg: generate(palette.FIDESUI_ERROR, {
        theme: "dark",
        backgroundColor: palette.FIDESUI_BG_MINOS,
      })[0],
      colorError: generate(palette.FIDESUI_ERROR, {
        theme: "dark",
        backgroundColor: palette.FIDESUI_BG_MINOS,
      })[4],
    },
    Layout: {
      bodyBg: palette.FIDESUI_NEUTRAL_1000,
    },
    Card: {
      colorBgContainer: palette.FIDESUI_MINOS,
    },
  },
};
