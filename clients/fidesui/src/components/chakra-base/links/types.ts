import { LinkProps as ChakraLinkProps } from "fidesui";

export type LinkProps = ChakraLinkProps & {
  isDisabled?: boolean;
  isActive?: boolean;
};
