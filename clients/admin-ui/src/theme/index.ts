import { extendTheme } from "@fidesui/react";

import Button from "~/theme/components/button";

const theme = extendTheme({
  styles: {
    global: {
      body: {
        bg: "white",
      },
      html: {
        height: "100%",
      },
    },
  },
  components: {
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
