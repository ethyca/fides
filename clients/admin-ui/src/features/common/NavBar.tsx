import { Button, Flex } from "@fidesui/react";
import NextLink from "next/link";
import { useRouter } from "next/router";
import { useSession } from "next-auth/react";
import React, { ReactElement } from "react";

import { ArrowDownLineIcon } from "@/features/common/Icon";

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
      >
        {title}
      </Button>
    </NextLink>
  );
};

const NavBar = () => {
  const { data: session } = useSession();
  const username: string | any = session?.username;

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
          <NavLink title="Taxonomy" href="/taxonomy" disabled />
          <NavLink title="User Management" href="/user-management" disabled />
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
