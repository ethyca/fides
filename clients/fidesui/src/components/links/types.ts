import { LinkProps as ChakraLinkProps } from "@fidesui/react";

export type LinkProps = ChakraLinkProps & {
  isDisabled?: boolean;
  isActive?: boolean;
};
