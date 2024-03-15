import { extendTheme } from "@fidesui/react";

import Button from "~/theme/components/button";

const theme = extendTheme({
  styles: {
    global: {
      body: {
        bg: "white",
        minWidth: "container.lg",
        height: "100%",
      },
      html: {
        height: "100%",
      },
      "#__next": {
        height: "100%",
      },
    },
  },
  components: {
    Accordion: {
      baseStyle: {
        button: {
          // Remove annoying focus outline, unless for a11y visibility
          // NOTE: Upgrading to Chakra 2.2.0+ will fix this globally:
          // (see https://chakra-ui.com/changelog/2.2.0#all-components)
          _focus: { boxShadow: "none" },
          _focusVisible: { boxShadow: "outline" },
        },
      },
    },
    Button,
    Divider: {
      baseStyle: {
        opacity: 1,
      },
    },
    Spinner: {
      baseStyle: {
        color: "secondary.500",
      },
      defaultProps: {
        size: "xl",
      },
    },
    Switch: {
      baseStyle: {
        track: {
          _focus: {
            boxShadow: "none",
            outline: "2px solid #272B53",
          },
        },
      },
    },
  },
});

export default theme;
