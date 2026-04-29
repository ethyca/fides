import { ThemeConfig } from "antd/es";

import { palette } from "../palette/palette";

/**
 * Order of priority for styling
 * 1. Ant Design default theme
 * 2. FidesUI palette colors
 * 3. Ant Design custom theme (this file, which also includes some custom override colors not found in the palette)
 * 4. global CSS variables (as a last resort when styling Ant components, should rely on the palette vars)
 * 5. tailwindcss (for layout and spacing only)
 * 6. SCSS modules (for custom-component-specific styles)
 */

// Custom keys are picked up by Ant's `transformToken` (via `cssVar`) and
// emitted as CSS vars alongside built-ins, so they participate in dark mode.
const brandTokens = {
  brandMinos: palette.FIDESUI_MINOS,
  brandBgMinos: palette.FIDESUI_BG_MINOS,
  brandCorinth: palette.FIDESUI_CORINTH,
  brandBgCorinth: palette.FIDESUI_BG_CORINTH,
  brandLimestone: palette.FIDESUI_LIMESTONE,
  brandTerracotta: palette.FIDESUI_TERRACOTTA,
  brandBgTerracotta: palette.FIDESUI_BG_TERRACOTTA,
  brandOlive: palette.FIDESUI_OLIVE,
  brandBgOlive: palette.FIDESUI_BG_OLIVE,
  brandMarble: palette.FIDESUI_MARBLE,
  brandBgMarble: palette.FIDESUI_BG_MARBLE,
  brandSandstone: palette.FIDESUI_SANDSTONE,
  brandBgSandstone: palette.FIDESUI_BG_SANDSTONE,
  brandNectar: palette.FIDESUI_NECTAR,
  brandBgNectar: palette.FIDESUI_BG_NECTAR,
  brandAlert: palette.FIDESUI_ALERT,
  brandBgAlert: palette.FIDESUI_BG_ALERT,
  brandBgCaution: palette.FIDESUI_BG_CAUTION,
  brandBgError: palette.FIDESUI_BG_ERROR,
  brandBgWarning: palette.FIDESUI_BG_WARNING,
  brandBgSuccess: palette.FIDESUI_BG_SUCCESS,
  brandBgInfo: palette.FIDESUI_BG_INFO,
  brandErrorText: palette.FIDESUI_ERROR_TEXT,
  brandSuccessText: palette.FIDESUI_SUCCESS_TEXT,
};

const neutralTokens = {
  neutral50: palette.FIDESUI_NEUTRAL_50,
  neutral75: palette.FIDESUI_NEUTRAL_75,
  neutral100: palette.FIDESUI_NEUTRAL_100,
  neutral200: palette.FIDESUI_NEUTRAL_200,
  neutral300: palette.FIDESUI_NEUTRAL_300,
  neutral400: palette.FIDESUI_NEUTRAL_400,
  neutral500: palette.FIDESUI_NEUTRAL_500,
  neutral600: palette.FIDESUI_NEUTRAL_600,
  neutral700: palette.FIDESUI_NEUTRAL_700,
  neutral800: palette.FIDESUI_NEUTRAL_800,
  neutral900: palette.FIDESUI_NEUTRAL_900,
};

export const defaultAntTheme: ThemeConfig = {
  cssVar: { prefix: "fidesui", key: "fidesui" },
  token: {
    fontFamily: `"Basier Square", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
    fontFamilyCode: `"Basier Square Mono", "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace`,
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
    borderRadiusSM: 4,
    borderRadius: 6,
    borderRadiusLG: 6,
    colorErrorBg: "#ffdcd6", // custom override
    colorErrorBorder: "#f2aca5", // custom override
    colorWarningBg: "#ffecc9", // custom override
    colorWarningBorder: "#ffdba1", // custom override
    colorSuccessBorder: palette.FIDESUI_SUCCESS,
    colorPrimaryBg: palette.FIDESUI_NEUTRAL_75,
    colorBorder: palette.FIDESUI_NEUTRAL_100,
    colorBorderSecondary: palette.FIDESUI_NEUTRAL_100,
    colorSplit: palette.FIDESUI_NEUTRAL_100,
    zIndexPopupBase: 1500, // supersede Chakra's modal z-index
    ...brandTokens,
    ...neutralTokens,
  },
  components: {
    Avatar: {
      colorTextPlaceholder: palette.FIDESUI_BG_DEFAULT,
    },
    Alert: {
      colorInfo: palette.FIDESUI_MINOS,
      colorInfoBg: palette.FIDESUI_NEUTRAL_50,
      colorInfoBorder: palette.FIDESUI_NEUTRAL_100,
      // Ant bumps the title to `fontSizeLG` (16) when a description is present;
      // pin it back to the body size so alerts don't grow a larger heading.
      fontSizeLG: 14,
    },
    Button: {
      primaryShadow: undefined,
      defaultShadow: undefined,
      dangerShadow: undefined,
      defaultBg: palette.FIDESUI_FULL_WHITE,
      textHoverBg: undefined,
      textTextHoverColor: palette.FIDESUI_NEUTRAL_600,
    },
    Card: {
      borderRadiusLG: 8,
    },
    Drawer: {
      zIndexPopupBase: 1300, // below chakra's modal (so the contents of a drawer can open a modal eg. data map drawer)
    },
    Input: {
      colorBgContainer: palette.FIDESUI_FULL_WHITE,
      colorBorderDisabled: palette.FIDESUI_NEUTRAL_100,
      colorTextDisabled: palette.FIDESUI_NEUTRAL_700,
      colorBgContainerDisabled: palette.FIDESUI_NEUTRAL_50,
    },
    Layout: {
      bodyBg: palette.FIDESUI_NEUTRAL_50,
    },
    Dropdown: {
      controlItemBgActiveHover: palette.FIDESUI_NEUTRAL_50,
      controlItemBgHover: palette.FIDESUI_NEUTRAL_50,
    },
    Menu: {
      itemHoverBg: palette.FIDESUI_NEUTRAL_50,
      controlItemBgActiveHover: palette.FIDESUI_NEUTRAL_50,
      controlItemBgHover: palette.FIDESUI_NEUTRAL_50,
      darkItemBg: palette.FIDESUI_MINOS,
      darkItemColor: palette.FIDESUI_CORINTH,
      darkSubMenuItemBg: palette.FIDESUI_MINOS,
      darkItemSelectedBg: palette.FIDESUI_SANDSTONE,
    },
    Popover: {
      colorText: "inherit", // Ant v6 Popover gets its text color from the Tooltip component, which we have set to a dark background and light text. Popovers typically use light backgrounds, so we need to override the text color to ensure readability. For some reason, using `palette.FIDESUI_MINOS` here will not work??
    },
    Select: {
      optionActiveBg: palette.FIDESUI_NEUTRAL_50,
    },
    Table: {
      cellPaddingBlockSM: 8,
      cellPaddingInlineSM: 16,
      cellFontSizeSM: 12,
      rowSelectedBg: palette.FIDESUI_NEUTRAL_50,
      rowSelectedHoverBg: palette.FIDESUI_NEUTRAL_75,
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
      titleMarginBottom: 0,
      fontSizeXL: 24,
      fontSizeLG: 18,
      fontSizeSM: 12,
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
