import { extendTheme } from "@fidesui/react";

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
});

export default theme;
