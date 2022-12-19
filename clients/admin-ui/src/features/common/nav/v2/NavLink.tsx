import { PrimaryLink, SecondaryLink } from "@fidesui/components";
import NextLink from "next/link";
import React, { ReactNode } from "react";

interface Props {
  children: ReactNode;
  href: string;
  isActive?: boolean;
  isDisabled?: boolean;
}

export const NavLink = ({
  variant,
  children,
  href,
  isActive,
  isDisabled,
}: Props & { variant: "primary" | "secondary" }) => {
  const LinkComponent = variant === "primary" ? PrimaryLink : SecondaryLink;

  // Don't let Next's router wrap links that are disabled.
  if (isDisabled) {
    return (
      <LinkComponent isDisabled={isDisabled} href={href} isActive={isActive}>
        {children}
      </LinkComponent>
    );
  }

  return (
    <NextLink href={href} passHref>
      <LinkComponent isActive={isActive}>{children}</LinkComponent>
    </NextLink>
  );
};

export const NavTopBarLink = (props: Props) => (
  <NavLink variant="primary" {...props} />
);

export const NavSideBarLink = (props: Props) => (
  <NavLink variant="secondary" {...props} />
);
