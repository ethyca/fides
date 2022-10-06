import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { ReactElement } from "react";

import { NavButton } from "./NavButton";
import { resolveLink } from "./zone-config";

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

  // Next's router returns an empty string for the root base path, even the documentation refers the
  // root base path as "/".
  const basePath = router.basePath || "/";

  const zoneLink = resolveLink({
    href,
    basePath,
  });

  const isActive = exact
    ? router.pathname === zoneLink.href
    : router.pathname.startsWith(zoneLink.href);

  // Don't let Next's router wrap links that are disabled or link outside of the this app's zone.
  if (disabled || zoneLink.basePath !== basePath) {
    return (
      <NavButton
        disabled={disabled}
        href={zoneLink.href}
        isActive={isActive}
        rightIcon={rightIcon}
        title={title}
      />
    );
  }

  return (
    <NextLink href={zoneLink.href} passHref>
      <NavButton isActive={isActive} rightIcon={rightIcon} title={title} />
    </NextLink>
  );
};

export default NavLink;
