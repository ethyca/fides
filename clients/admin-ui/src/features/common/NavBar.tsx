import { Button, Flex } from "@fidesui/react";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useSession } from "next-auth/react";
import React, { ReactElement } from "react";

import { ArrowDownLineIcon } from "~/features/common/Icon";

import Header from "./Header";

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
  return (
    <NextLink href={href} passHref>
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
    </NextLink>
  );
};

const NavBar = () => {
  const { data: session } = useSession();
  // TODO: what should be displayed if there is no user name?
  const username = session?.user?.name ?? "";

  return (
    <>
      <Header username={username} />
      <Flex
        borderBottom="1px"
        borderTop="1px"
        px={9}
        py={1}
        borderColor="gray.100"
      >
        <nav>
          <NavLink title="Systems" href="/system" />
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
    </>
  );
};

export default NavBar;
