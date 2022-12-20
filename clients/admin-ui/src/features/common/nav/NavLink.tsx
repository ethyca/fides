import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { ReactElement } from "react";

import { NavButton } from "./NavButton";
import { resolveZoneLink } from "./zone-config";

interface NavLinkProps {
  title: string;
  href: string;
  disabled?: boolean;
  rightIcon?: ReactElement;
  exact?: boolean;
}

export const NavLink = ({
  title,
  href,
  disabled,
  rightIcon,
  exact,
}: NavLinkProps) => {
  const router = useRouter();
  const zoneLink = resolveZoneLink({ href, router, exact });

  // Don't let Next's router wrap links that are disabled or link outside of the this app's zone.
  if (disabled || !zoneLink.isCurrentZone) {
    return (
      <NavButton
        disabled={disabled}
        href={zoneLink.href}
        isActive={zoneLink.isActive}
        rightIcon={rightIcon}
        title={title}
      />
    );
  }

  return (
    <NextLink href={zoneLink.href} passHref>
      <NavButton
        isActive={zoneLink.isActive}
        rightIcon={rightIcon}
        title={title}
      />
    </NextLink>
  );
};

export default NavLink;
