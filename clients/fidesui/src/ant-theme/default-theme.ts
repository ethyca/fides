import { ThemeConfig } from "antd/es";

import palette from "../palette/palette.module.scss";

/**
 * Order of priority for styling
 * 1. Ant Design default theme
 * 2. FidesUI palette colors
 * 3. Ant Design custom theme (this file, which also includes some custom override colors not found in the palette)
 * 4. global CSS variables (as a last resort when styling Ant components, should rely on the palette vars)
 * 5. tailwindcss (for layout and spacing only)
 * 6. SCSS modules (for custom-component-specific styles)
 */

export const defaultAntTheme: ThemeConfig = {
  cssVar: true,
  token: {
    fontFamily: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
    colorText: palette.FIDESUI_MINOS,
    colorTextBase: palette.FIDESUI_MINOS,
    colorTextHeading: palette.FIDESUI_MINOS,
    colorTextDescription: palette.FIDESUI_NEUTRAL_700, // minimum for accessibility
    colorTextDisabled: palette.FIDESUI_NEUTRAL_400,
    colorPrimary: palette.FIDESUI_MINOS,
    colorInfo: palette.FIDESUI_MINOS,
    colorSuccess: palette.FIDESUI_SUCCESS,
    colorWarning: palette.FIDESUI_WARNING,
    colorError: palette.FIDESUI_ERROR,
    colorLink: palette.FIDESUI_LINK,
    colorBgBase: palette.FIDESUI_FULL_WHITE,
    borderRadius: 4,
    wireframe: true,
    colorErrorBg: "#ffdcd6", // custom override
    colorErrorBorder: "#f2aca5", // custom override
    colorWarningBg: "#ffecc9", // custom override
    colorWarningBorder: "#ffdba1", // custom override
    colorSuccessBorder: palette.FIDESUI_SUCCESS,
    colorPrimaryBg: palette.FIDESUI_NEUTRAL_75,
    colorBorder: palette.FIDESUI_NEUTRAL_100,
    zIndexPopupBase: 1500, // supersede Chakra's modal z-index
  },
  components: {
    Alert: {
      colorInfoBg: palette.FIDESUI_FULL_WHITE,
      colorInfo: palette.FIDESUI_NEUTRAL_500,
    },
    Button: {
      primaryShadow: undefined,
      defaultShadow: undefined,
      dangerShadow: undefined,
      defaultBg: palette.FIDESUI_FULL_WHITE,
    },
    Card: {
      colorBorderSecondary: palette.FIDESUI_NEUTRAL_200,
    },
    Input: {
      colorBgContainer: palette.FIDESUI_FULL_WHITE,
    },
    Layout: {
      bodyBg: palette.FIDESUI_NEUTRAL_50,
    },
    Select: {
      optionActiveBg: palette.FIDESUI_NEUTRAL_50,
    },
    Menu: {
      itemHoverBg: palette.FIDESUI_NEUTRAL_50,
      darkItemBg: palette.FIDESUI_MINOS,
      darkItemColor: palette.FIDESUI_CORINTH,
      darkSubMenuItemBg: palette.FIDESUI_MINOS,
      darkItemSelectedBg: palette.FIDESUI_SANDSTONE,
    },
    Table: {
      cellPaddingBlockSM: 8,
      cellPaddingInlineSM: 16,
      cellFontSizeSM: 12,
    },
    Tooltip: {
      colorBgSpotlight: palette.FIDESUI_MINOS,
      colorText: palette.FIDESUI_NEUTRAL_50,
      colorTextLightSolid: palette.FIDESUI_NEUTRAL_50,
    },
    Transfer: {
      controlItemBgActiveHover: palette.FIDESUI_SANDSTONE,
    },
    Typography: {
      fontSizeHeading1: 24,
      fontSizeHeading2: 20,
      fontSizeHeading3: 16,
      fontSizeXL: 24,
      fontSizeLG: 18,
      fontSizeSM: 12,
      titleMarginBottom: 0,
    },
    Tag: {
      colorText: palette.FIDESUI_NEUTRAL_900,
      colorIcon: palette.FIDESUI_NEUTRAL_700,
      colorIconHover: palette.FIDESUI_NEUTRAL_900,
    },
  },
};

/**
 * Factory function to create customized Ant themes
 * Allows for deep merging of theme overrides
 */
export const createDefaultAntTheme = (
  overrides?: Partial<ThemeConfig>,
): ThemeConfig => ({
  ...defaultAntTheme,
  ...overrides,
  token: {
    ...defaultAntTheme.token,
    ...overrides?.token,
  },
  components: {
    ...defaultAntTheme.components,
    ...overrides?.components,
  },
});
