import { AntThemeConfig } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

/**
 * Order of priority for styling
 * 1. Ant Design default theme
 * 2. FidesUI palette colors
 * 3. Ant Design custom theme (this file, which also includes some custom override colors not found in the palette)
 * 4. global CSS variables (as a last resort when styling Ant components, should rely on the palette vars)
 * 5. tailwindcss (for layout and spacing only)
 * 6. SCSS modules (for custom-component-specific styles)
 */

export const antTheme: AntThemeConfig = {
  cssVar: true,
  token: {
    fontFamily: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
    colorPrimary: palette.FIDESUI_MINOS,
    colorInfo: palette.FIDESUI_MINOS,
    colorSuccess: palette.FIDESUI_SUCCESS,
    colorWarning: palette.FIDESUI_WARNING,
    colorError: palette.FIDESUI_ERROR,
    colorLink: palette.FIDESUI_LINK,
    colorBgBase: palette.FIDESUI_FULL_WHITE,
    borderRadius: 4,
    wireframe: true,
    colorTextBase: palette.FIDESUI_MINOS,
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
    Dropdown: {
      fontSize: 16,
      paddingBlock: 8,
    },
    Tooltip: {
      colorBgSpotlight: palette.FIDESUI_MINOS,
      colorText: palette.FIDESUI_NEUTRAL_50,
      colorTextLightSolid: palette.FIDESUI_NEUTRAL_50,
    },
    Transfer: {
      controlItemBgActiveHover: palette.FIDESUI_SANDSTONE,
    },
  },
};
