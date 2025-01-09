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
  border: `1px solid ${palette.FIDESUI_NEUTRAL_75}`,
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
    secondary: {
      50: "#E4FBF2",
      100: "#BCF5DD",
      200: "#8FEFC7",
      300: "#62E9B1",
      400: "#41E4A0",
      500: "#1FDF8F",
      600: "#1BDB87",
      700: "#17D77C",
      800: "#12D272",
      900: "#0ACA60",
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
    minos: {
      500: "#2b2e35",
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
