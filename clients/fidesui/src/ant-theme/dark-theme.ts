import { generate } from "@ant-design/colors";
import { theme, ThemeConfig } from "antd";

import palette from "../palette/palette.module.scss";
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

export const darkAntTheme: ThemeConfig = {
  ...defaultAntTheme,
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
    Layout: {
      bodyBg: palette.FIDESUI_BG_MINOS,
    },
    Card: {
      colorBgContainer: palette.FIDESUI_MINOS,
    },
  },
};
