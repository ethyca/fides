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
  token: {
    ...defaultAntTheme.token,
    colorBgBase: palette.FIDESUI_BG_MINOS,
    colorTextBase: palette.FIDESUI_CORINTH,
    colorText: palette.FIDESUI_CORINTH,
    colorTextHeading: palette.FIDESUI_CORINTH,
    colorPrimary: palette.FIDESUI_CORINTH,
    colorBgContainer: palette.FIDESUI_BG_MINOS,
    colorBorder: generate(palette.FIDESUI_MINOS, {
      theme: "dark",
      backgroundColor: palette.FIDESUI_BG_MINOS,
    })[4],
    colorErrorBg: generate(palette.FIDESUI_ERROR, {
      theme: "dark",
      backgroundColor: palette.FIDESUI_BG_MINOS,
    })[1],
    colorErrorBorder: generate(palette.FIDESUI_ERROR, {
      theme: "dark",
      backgroundColor: palette.FIDESUI_BG_MINOS,
    })[3],
    colorWarningBg: generate(palette.FIDESUI_WARNING, {
      theme: "dark",
      backgroundColor: palette.FIDESUI_BG_MINOS,
    })[1],
    colorWarningBorder: generate(palette.FIDESUI_WARNING, {
      theme: "dark",
      backgroundColor: palette.FIDESUI_BG_MINOS,
    })[3],
  },
  components: {
    ...defaultAntTheme.components,
    Layout: {
      bodyBg: palette.FIDESUI_BG_MINOS,
    },
    Card: {
      colorBgContainer: palette.FIDESUI_MINOS,
    },
  },
};
