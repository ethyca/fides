import { ComponentStyleConfig } from "@chakra-ui/react";

const theme: ComponentStyleConfig = {
  variants: {
    /**
     * This variant should be unnecessary: Chakra's "solid" variant accomplishes the same thing
     * using any color scheme. However, the "primary" color scheme from fidesui does not have enough
     * contrast between the color states that Chakra uses:
     *   - background = 500
     *   - hover = 600
     *   - active = 700
     */
    primary: {
      bg: "primary.800",
      color: "white",
      _hover: {
        bg: "primary.400",
        _disabled: {
          bg: "primary.800",
        },
      },
      _active: { bg: "primary.500" },
    },
  },
};

export default theme;
