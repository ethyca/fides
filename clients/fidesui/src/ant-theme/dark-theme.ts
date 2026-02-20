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
    colorTextDescription: palette.FIDESUI_NEUTRAL_400,
    colorTextDisabled: palette.FIDESUI_NEUTRAL_600,
    colorPrimary: palette.FIDESUI_CORINTH,
    colorInfo: palette.FIDESUI_CORINTH,
    colorLink: "#5b9bd5",
    colorBorder: "#3a3a3a",
    colorBorderSecondary: "#303030",
    colorSplit: "#303030",
    colorPrimaryBg: palette.FIDESUI_BG_MINOS,
    colorBgContainer: palette.FIDESUI_BG_MINOS,
  },
  components: {
    ...defaultAntTheme.components,
    Avatar: {
      colorTextPlaceholder: palette.FIDESUI_NEUTRAL_700,
    },
    Alert: {
      colorInfoBg: "#1f1f1f",
      colorInfo: palette.FIDESUI_NEUTRAL_400,
    },
    Button: {
      primaryShadow: undefined,
      defaultShadow: undefined,
      dangerShadow: undefined,
      defaultBg: "#1f1f1f",
      textHoverBg: undefined,
      textTextHoverColor: palette.FIDESUI_NEUTRAL_300,
    },
    Card: {
      ...defaultAntTheme.components?.Card,
      boxShadow: "rgba(255, 255, 255, 1) 0px 5px 5px",
    },
    Input: {
      colorBgContainer: "#1f1f1f",
    },
    Layout: {
      bodyBg: palette.FIDESUI_BG_MINOS,
    },
    Select: {
      optionActiveBg: "#2a2a2a",
    },
    Table: {
      ...defaultAntTheme.components?.Table,
      rowSelectedBg: "#1a1a2e",
      rowSelectedHoverBg: "#222240",
    },
    Tooltip: {
      colorBgSpotlight: palette.FIDESUI_CORINTH,
      colorText: palette.FIDESUI_MINOS,
      colorTextLightSolid: palette.FIDESUI_MINOS,
    },
    Transfer: {
      controlItemBgActiveHover: "#2a2a2a",
    },
    Tag: {
      colorText: palette.FIDESUI_NEUTRAL_200,
      colorIcon: palette.FIDESUI_NEUTRAL_400,
      colorIconHover: palette.FIDESUI_NEUTRAL_200,
    },
  },
};

/**
 * Factory function to create customized dark Ant themes.
 * Allows for deep merging of theme overrides on top of the dark base.
 */
export const createDarkAntTheme = (
  overrides?: Partial<ThemeConfig>,
): ThemeConfig => ({
  ...darkAntTheme,
  ...overrides,
  algorithm: overrides?.algorithm ?? darkAntTheme.algorithm,
  token: {
    ...darkAntTheme.token,
    ...overrides?.token,
  },
  components: {
    ...darkAntTheme.components,
    ...overrides?.components,
  },
});
