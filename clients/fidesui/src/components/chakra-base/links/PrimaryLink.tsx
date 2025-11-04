import { forwardRef } from "@chakra-ui/react";
import { Link } from "fidesui";
import React from "react";

import { LinkProps } from "./types";

const defaultProps: LinkProps = {
  color: "gray.700",
  fontWeight: "500",
  fontSize: "sm",
  borderRadius: "50px",
  paddingX: 3,
  paddingY: 1,
  _hover: {
    background: "gray.100",
  },
};
const activeProps: LinkProps = {
  background: "primary.800",
  color: "white",
  _hover: {
    background: "primary.500",
  },
};
const disabledProps: LinkProps = {
  color: "gray.500",
  _hover: {
    background: "unset",
    color: "gray.500",
    cursor: "not-allowed",
  },
};

export const PrimaryLink = forwardRef(
  ({ href, isDisabled, isActive, children, ...props }: LinkProps, ref) => {
    const styledProps: LinkProps = {
      ...defaultProps,
      ...(isActive ? activeProps : undefined),
      ...(isDisabled ? disabledProps : undefined),
      ...props,
    };
    return (
      <Link ref={ref} href={isDisabled ? undefined : href} {...styledProps}>
        {children}
      </Link>
    );
  },
);

export default PrimaryLink;
