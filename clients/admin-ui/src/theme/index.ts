import { extendTheme } from "@fidesui/react";

import Button from "~/theme/components/button";

const theme = extendTheme({
  styles: {
    global: {
      body: {
        bg: "white",
        minWidth: "container.lg",
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
  },
});

export default theme;
