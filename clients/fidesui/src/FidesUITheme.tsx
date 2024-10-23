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
      50: "#F0EAFD",
      100: "#DACAFB",
      200: "#C1A7F9",
      300: "#A883F6",
      400: "#9569F4",
      500: "#824EF2",
      600: "#7A47F0",
      700: "#6F3DEE",
      800: "#6535EC",
      900: "#5225E8",
    },
    minos: {
      500: "#2b2e35",
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
