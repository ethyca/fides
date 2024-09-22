import { extendTheme as extendChakraTheme } from "@chakra-ui/react";
import { Dict } from "@chakra-ui/utils";

// eslint-disable-next-line import/prefer-default-export
export const theme: Dict = extendChakraTheme({
  colors: {
    corinth: "#FAFAFA",
    limestone: "#F1EFEE",
    minos: "#2B2E35",
    terracotta: "#B9704B",
    olive: "#999B83",
    marble: "#CDD2D3",
    sandstone: "#CECAC2",
    nectar: "#F0EBC1",
    error: "#D9534F",
    warning: "#E59D47",
    success: "#5A9A68",
    blue: "#4A90E2",
    purple: "#7B4EA9",
    error_tag: "#F7C2C2",
    warning_tag: "#FBDDB5",
    success_tag: "#C3E6B2",
    blue_tag: "#A5D6F3",
    purple_tag: "#D9B0D7",
    yellow_tag: "#F6E3A4",
    minos_tag: "#4F525B",
    olive_tag: "#D4D5C8",
    sandstone_tag: "#E3E0D9",
    marble_tag: "#E1E5E6",
    nectar_tag: "#F5F2D7",
    corinth_tag: "#FAFAFA",
    terracota_tag: "#F1B193",
    white_tag: "#FFFFFF",
    error_text: "#D9534F",
    success_text: "#D9534F",
    black_text: "#000000",
    white_text: "#FFFFFF",
    hyperlink_text: "#2272CE",
    checkbox_colors: {
      50: "corinth",
      500: "minos",
      700: "minos_tag",
    },
    neutral: {
      50: "#FAFAFA",
      100: "#E6E6E8",
      200: "#D1D2D4",
      300: "#BCBEC1",
      400: "#A8AAAD",
      500: "#93969A",
      600: "#7E8185",
      700: "#696C71",
      800: "#53575C",
      850: "#373B44",
      900: "#2B2E35",
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
