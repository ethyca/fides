import {
  defineStyle,
  defineStyleConfig,
  extendTheme as extendChakraTheme,
} from "@chakra-ui/react";
import { Dict } from "@chakra-ui/utils";
import palette from "fidesui/src/palette/palette.module.scss";

// eslint-disable-next-line import/prefer-default-export

const subtleBadge = defineStyle((props) => ({
  bg: props.colorScheme
    ? `${props.colorScheme}.100`
    : palette.FIDESUI_NEUTRAL_100,
}));
const solidBadge = defineStyle({
  bg: palette.FIDESUI_MINOS,
  color: palette.FIDESUI_CORINTH,
});
const taxonomyBadge = defineStyle({
  bg: "transparent",
  border: `1px solid ${palette.FIDESUI_NEUTRAL_100}`,
});

const badgeTheme = defineStyleConfig({
  variants: {
    // default badge for most use cases
    subtle: subtleBadge,
    // to be used in when displaying taxonomy labels (data categories, uses and subjects)
    taxonomy: taxonomyBadge,
    // for backwards compatibility with previous styles
    solid: solidBadge,
  },
  baseStyle: {
    borderRadius: "4px",
    color: palette.FIDESUI_MINOS,
    paddingInlineStart: "var(--chakra-space-1-5)",
    paddingInlineEnd: "var(--chakra-space-1-5)",
    textTransform: "none",
    fontWeight: "normal",
  },
});

const inputTheme = defineStyleConfig({
  variants: {
    outline: {
      field: {
        // Remove blue highlight on focused inputs
        _focusVisible: {
          outline: 0,
          boxShadow: "none",
          borderColor: "initial",
        },
      },
    },
  },
});
const linkTheme = defineStyleConfig({
  baseStyle: {
    color: palette.FIDESUI_LINK,
  },
});
const checkboxTheme = defineStyleConfig({
  defaultProps: {
    colorScheme: "primary",
  },
});

export const theme: Dict = extendChakraTheme({
  colors: {
    primary: {
      50: palette.FIDESUI_BG_MINOS,
      100: palette.FIDESUI_BG_MINOS,
      200: palette.FIDESUI_BG_MINOS,
      300: palette.FIDESUI_MINOS,
      400: palette.FIDESUI_MINOS,
      500: palette.FIDESUI_MINOS,
      600: palette.FIDESUI_MINOS,
      700: palette.FIDESUI_MINOS,
      800: palette.FIDESUI_MINOS,
      900: palette.FIDESUI_MINOS,
    },
    complimentary: {
      50: palette.FIDESUI_BG_MINOS,
      100: palette.FIDESUI_BG_MINOS,
      200: palette.FIDESUI_BG_MINOS,
      300: palette.FIDESUI_MINOS,
      400: palette.FIDESUI_MINOS,
      500: palette.FIDESUI_MINOS,
      600: palette.FIDESUI_MINOS,
      700: palette.FIDESUI_MINOS,
      800: palette.FIDESUI_MINOS,
      900: palette.FIDESUI_MINOS,
    },
    terracotta: {
      50: palette.FIDESUI_BG_TERRACOTTA,
      100: palette.FIDESUI_BG_TERRACOTTA,
      200: palette.FIDESUI_BG_TERRACOTTA,
      300: palette.FIDESUI_TERRACOTTA,
      400: palette.FIDESUI_TERRACOTTA,
      500: palette.FIDESUI_TERRACOTTA,
      600: palette.FIDESUI_TERRACOTTA,
      700: palette.FIDESUI_TERRACOTTA,
      800: palette.FIDESUI_TERRACOTTA,
      900: palette.FIDESUI_TERRACOTTA,
    },
    sandstone: {
      50: palette.FIDESUI_BG_SANDSTONE,
      100: palette.FIDESUI_BG_SANDSTONE,
      200: palette.FIDESUI_BG_SANDSTONE,
      300: palette.FIDESUI_SANDSTONE,
      400: palette.FIDESUI_SANDSTONE,
      500: palette.FIDESUI_SANDSTONE,
      600: palette.FIDESUI_SANDSTONE,
      700: palette.FIDESUI_SANDSTONE,
      800: palette.FIDESUI_SANDSTONE,
      900: palette.FIDESUI_SANDSTONE,
    },
    olive: {
      50: palette.FIDESUI_BG_OLIVE,
      100: palette.FIDESUI_BG_OLIVE,
      200: palette.FIDESUI_BG_OLIVE,
      300: palette.FIDESUI_OLIVE,
      400: palette.FIDESUI_OLIVE,
      500: palette.FIDESUI_OLIVE,
      600: palette.FIDESUI_OLIVE,
      700: palette.FIDESUI_OLIVE,
      800: palette.FIDESUI_OLIVE,
      900: palette.FIDESUI_OLIVE,
    },
    marble: {
      50: palette.FIDESUI_BG_MARBLE,
      100: palette.FIDESUI_BG_MARBLE,
      200: palette.FIDESUI_BG_MARBLE,
      300: palette.FIDESUI_MARBLE,
      400: palette.FIDESUI_MARBLE,
      500: palette.FIDESUI_MARBLE,
      600: palette.FIDESUI_MARBLE,
      700: palette.FIDESUI_MARBLE,
      800: palette.FIDESUI_MARBLE,
      900: palette.FIDESUI_MARBLE,
    },
    nectar: {
      50: palette.FIDESUI_BG_NECTAR,
      100: palette.FIDESUI_BG_NECTAR,
      200: palette.FIDESUI_BG_NECTAR,
      300: palette.FIDESUI_NECTAR,
      400: palette.FIDESUI_NECTAR,
      500: palette.FIDESUI_NECTAR,
      600: palette.FIDESUI_NECTAR,
      700: palette.FIDESUI_NECTAR,
      800: palette.FIDESUI_NECTAR,
      900: palette.FIDESUI_NECTAR,
    },
    gray: {
      50: palette.FIDESUI_NEUTRAL_50,
      75: palette.FIDESUI_NEUTRAL_75,
      100: palette.FIDESUI_NEUTRAL_100,
      200: palette.FIDESUI_NEUTRAL_200,
      300: palette.FIDESUI_NEUTRAL_300,
      400: palette.FIDESUI_NEUTRAL_400,
      500: palette.FIDESUI_NEUTRAL_500,
      600: palette.FIDESUI_NEUTRAL_600,
      700: palette.FIDESUI_NEUTRAL_700,
      800: palette.FIDESUI_NEUTRAL_800,
      900: palette.FIDESUI_NEUTRAL_900,
    },
    warn: {
      100: palette.FIDESUI_BG_WARNING,
      200: palette.FIDESUI_BG_WARNING,
      300: palette.FIDESUI_WARNING,
      400: palette.FIDESUI_WARNING,
      500: palette.FIDESUI_WARNING,
      600: palette.FIDESUI_WARNING,
      700: palette.FIDESUI_WARNING,
      800: palette.FIDESUI_WARNING,
      900: palette.FIDESUI_WARNING,
    },
    info: {
      100: palette.FIDESUI_BG_INFO,
      200: palette.FIDESUI_BG_INFO,
      300: palette.FIDESUI_INFO,
      400: palette.FIDESUI_INFO,
      500: palette.FIDESUI_INFO,
      600: palette.FIDESUI_INFO,
      700: palette.FIDESUI_INFO,
      800: palette.FIDESUI_INFO,
      900: palette.FIDESUI_INFO,
    },
    alert: {
      100: palette.FIDESUI_BG_ALERT,
      200: palette.FIDESUI_BG_ALERT,
      300: palette.FIDESUI_ALERT,
      400: palette.FIDESUI_ALERT,
      500: palette.FIDESUI_ALERT,
      600: palette.FIDESUI_ALERT,
      700: palette.FIDESUI_ALERT,
      800: palette.FIDESUI_ALERT,
      900: palette.FIDESUI_ALERT,
    },
    success: {
      100: palette.FIDESUI_BG_SUCCESS,
      200: palette.FIDESUI_BG_SUCCESS,
      300: palette.FIDESUI_SUCCESS,
      400: palette.FIDESUI_SUCCESS,
      500: palette.FIDESUI_SUCCESS,
      600: palette.FIDESUI_SUCCESS,
      700: palette.FIDESUI_SUCCESS,
      800: palette.FIDESUI_SUCCESS,
      900: palette.FIDESUI_SUCCESS,
    },
    error: {
      100: palette.FIDESUI_BG_ERROR,
      200: palette.FIDESUI_BG_ERROR,
      300: palette.FIDESUI_ERROR,
      400: palette.FIDESUI_ERROR,
      500: palette.FIDESUI_ERROR,
      600: palette.FIDESUI_ERROR,
      700: palette.FIDESUI_ERROR,
      800: palette.FIDESUI_ERROR,
      900: palette.FIDESUI_ERROR,
    },
    caution: {
      100: palette.FIDESUI_BG_CAUTION,
      200: palette.FIDESUI_BG_CAUTION,
      300: palette.FIDESUI_BG_CAUTION,
      400: palette.FIDESUI_BG_CAUTION,
      500: palette.FIDESUI_BG_CAUTION,
      600: palette.FIDESUI_BG_CAUTION,
      700: palette.FIDESUI_BG_CAUTION,
      800: palette.FIDESUI_BG_CAUTION,
      900: palette.FIDESUI_BG_CAUTION,
    },
    "success-text": {
      900: palette.FIDESUI_SUCCESS_TEXT,
    },
    "error-text": {
      900: palette.FIDESUI_ERROR_TEXT,
    },
    link: {
      900: palette.FIDESUI_LINK,
    },
  },
  fonts: {
    heading: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
    body: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
  },
  styles: {
    global: {
      body: {
        bg: "gray.100",
        color: palette.FIDESUI_MINOS,
      },
    },
  },
  components: {
    Badge: badgeTheme,
    Input: inputTheme,
    Link: linkTheme,
    Checkbox: checkboxTheme,
  },
});

// Wrap the Chakra extendTheme function in our own extendTheme function which
// extends our base theme already, so that if a consumer wants to extend their
// theme they won't lose the pre-existing Fides-specific customizations
export const extendTheme: (
  // eslint-disable-next-line no-unused-vars
  ...extensions: (Dict<any> | ((extendedTheme: Dict<any>) => Dict<any>))[]
) => Dict<any> = (
  // eslint-disable-next-line no-unused-vars
  ...extensions: (Dict<any> | ((extendedTheme: Dict<any>) => Dict<any>))[]
) => extendChakraTheme(theme, ...extensions);
