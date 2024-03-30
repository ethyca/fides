import { extendTheme as extendChakraTheme } from "@chakra-ui/react";
import { Dict } from "@chakra-ui/utils";

// eslint-disable-next-line import/prefer-default-export
export const theme: Dict = extendChakraTheme({
  colors: {
    primary: {
      50: "#E2E3E7",
      100: "#B8B9C4",
      200: "#888A9C",
      300: "#62668F",
      400: "#464B83",
      500: "#2B2E5C",
      600: "#272B53",
      700: "#20244B",
      800: "#111439",
      900: "#0D1031",
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
      50: "#EBF8FF",
      100: "#BEE3F8",
      200: "#90CDF4",
      300: "#63B3ED",
      400: "#4299E1",
      500: "#3182CE",
      600: "#2B6CB0",
      700: "#2C5282",
      800: "#2A4365",
      900: "#1A365D",
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
