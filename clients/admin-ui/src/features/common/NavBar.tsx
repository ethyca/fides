import { Button, Flex } from "@fidesui/react";
import NextLink from "next/link";
import { useRouter } from "next/router";
import React, { ReactElement } from "react";

import {
  DATASTORE_CONNECTION_ROUTE,
  INDEX_ROUTE,
  USER_MANAGEMENT_ROUTE,
} from "~/constants";
import Header from "./Header";
import { ArrowDownLineIcon } from "./Icon";

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
  const NavButton = (
    <Button
      as="a"
      variant="ghost"
      disabled={disabled}
      mr={4}
      colorScheme={isActive ? "complimentary" : "ghost"}
      rightIcon={rightIcon}
      data-testid={`nav-link-${title}`}
      isActive={isActive}
      _active={{ bg: "transparent" }}
    >
      {title}
    </Button>
  );
  if (disabled) {
    return NavButton;
  }
  return (
    <NextLink href={href} passHref>
      {NavButton}
    </NextLink>
  );
};

const NavBar = () => (
    <>
      <Header />
      <Flex
        borderBottom="1px"
        borderTop="1px"
        px={9}
        py={1}
        borderColor="gray.100"
      >
        <nav>
          <NavLink title="Subject Requests" href={INDEX_ROUTE} exact />
          <NavLink
            title="Datastore Connections"
            href={DATASTORE_CONNECTION_ROUTE}
          />
          <NavLink title="User Management" href={USER_MANAGEMENT_ROUTE} />
          <NavLink title="Systems" href="/system" disabled />
          <NavLink title="Datasets" href="/dataset" />
          <NavLink title="Policies" href="/policy" disabled />
          <NavLink title="Taxonomy" href="/taxonomy" />
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
    </>
  );

export default NavBar;
