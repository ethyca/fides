import { extendTheme } from "@fidesui/react";

import Button from "./components/button";

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
  },
});

export default theme;
