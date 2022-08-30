import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { ReactElement } from "react";

import { NavButton } from "./NavButton";

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
  let isActive = false;
  if (exact) {
    isActive = router.pathname === href;
  } else {
    isActive = router.pathname.startsWith(href);
  }

  if (disabled) {
    return (
      <NavButton
        disabled={disabled}
        isActive={isActive}
        rightIcon={rightIcon}
        title={title}
      />
    );
  }

  return (
    <NextLink href={href} passHref>
      <NavButton isActive={isActive} rightIcon={rightIcon} title={title} />
    </NextLink>
  );
};

export default NavLink;
