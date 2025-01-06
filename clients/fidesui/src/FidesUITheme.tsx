import { extendTheme as extendChakraTheme } from "@chakra-ui/react";
import { Dict } from "@chakra-ui/utils";
import palette from "fidesui/src/palette/palette.module.scss";

// eslint-disable-next-line import/prefer-default-export
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
    gray: {
      50: palette.FIDESUI_NEUTRAL_50,
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
  },
  fonts: {
    heading: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
    body: `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"`,
  },
  styles: {
    global: {
      body: {
        bg: "gray.100",
      },
    },
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
