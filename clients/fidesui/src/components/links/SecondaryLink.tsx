import { forwardRef } from "@chakra-ui/react";
import { Link } from "fidesui";
import React from "react";

import { LinkProps } from "./types";

const defaultProps: LinkProps = {
  color: "gray.700",
  fontWeight: "500",
  fontSize: "sm",
  _hover: {
    color: "gray.500",
  },
};
const activeProps: LinkProps = {
  color: "complimentary.500",
  _hover: {
    color: "complimentary.300",
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

export const SecondaryLink = forwardRef(
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

export default SecondaryLink;
