import { extendTheme as extendChakraTheme } from "@chakra-ui/react";
import { Dict } from "@chakra-ui/utils";

// eslint-disable-next-line import/prefer-default-export
export const theme: Dict = extendChakraTheme({
  colors: {
    primary: {
      50: "#FAFAFA",
      100: "#E6E6E8",
      200: "#D1D2D4",
      300: "#BCBEC1",
      400: "#A8AAAD",
      500: "#93969A",
      600: "#7E8185",
      700: "#696C71",
      800: "#53575C",
      900: "#2B2E35",
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
      50: "#CECAC2",
      100: "#CECAC2",
      200: "#CECAC2",
      300: "#CECAC2",
      400: "#CECAC2",
      500: "#CECAC2",
      600: "#CECAC2",
      700: "#CECAC2",
      800: "#CECAC2",
      900: "#CECAC2",
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
