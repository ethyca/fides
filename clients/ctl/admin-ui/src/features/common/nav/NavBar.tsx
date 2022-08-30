import { Flex } from "@fidesui/react";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { ReactElement } from "react";

import { ArrowDownLineIcon } from "~/features/common/Icon";

import { NavButton } from "./NavButton";

interface NavLinkProps {
  title: string;
  href: string;
  disabled?: boolean;
  rightIcon?: ReactElement;
  exact?: boolean;
}

const NavLink = ({ title, href, disabled, rightIcon, exact }: NavLinkProps) => {
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

const NavBar = () => (
  <Flex borderBottom="1px" borderTop="1px" px={9} py={1} borderColor="gray.100">
    <nav>
      <NavLink title="Systems" href="/system" disabled />
      <NavLink title="Datasets" href="/dataset" />
      <NavLink title="Policies" href="/policy" disabled />
      <NavLink title="Taxonomy" href="/taxonomy" />
      <NavLink title="User Management" href="/user-management" disabled />
      {/* This is a temporary link to the config wizard while it's still in progress */}
      <NavLink title="Config Wizard" href="/config-wizard" />
      <NavLink
        title="More"
        href="#"
        rightIcon={<ArrowDownLineIcon />}
        disabled
      />
    </nav>
  </Flex>
);

export default NavBar;
