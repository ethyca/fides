import { PrimaryLink, SecondaryLink } from "@fidesui/components";
import NextLink from "next/link";
import React, { ReactNode } from "react";

interface Props {
  children: ReactNode;
  dataTestId?: string;
  href: string;
  isActive?: boolean;
  isDisabled?: boolean;
}

export const NavLink = ({
  children,
  dataTestId,
  href,
  isActive,
  isDisabled,
  variant,
}: Props & { variant: "primary" | "secondary" }) => {
  const LinkComponent = variant === "primary" ? PrimaryLink : SecondaryLink;

  // Don't let Next's router wrap links that are disabled.
  if (isDisabled) {
    return (
      <LinkComponent
        data-testid={dataTestId}
        href={href}
        isActive={isActive}
        isDisabled={isDisabled}
      >
        {children}
      </LinkComponent>
    );
  }

  return (
    <NextLink href={href} passHref>
      <LinkComponent data-testid={dataTestId} isActive={isActive}>
        {children}
      </LinkComponent>
    </NextLink>
  );
};

export const NavTopBarLink = (props: Props) => (
  <NavLink variant="primary" {...props} />
);

export const NavSideBarLink = (props: Props) => (
  <NavLink variant="secondary" {...props} />
);
