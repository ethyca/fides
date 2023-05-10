import { NavList } from "@fidesui/components";
import { Heading, ListItem, UnorderedList, VStack } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { useNav } from "./hooks";
import type { ActiveNav, NavGroup, NavGroupChild } from "./nav-config";
import { NavSideBarLink } from "./NavLink";

const NavListItem = ({
  title,
  path,
  children,
  routerPathname,
}: NavGroupChild & { routerPathname: string }) => {
  const isActive = routerPathname.startsWith(path);

  return (
    <>
      <NavSideBarLink href={path} isActive={isActive}>
        {title}
      </NavSideBarLink>
      {children.length ? (
        <UnorderedList py={0.5}>
          {children.map((childRoute) => (
            <ListItem key={childRoute.title} listStyleType="none">
              <NavListItem routerPathname={routerPathname} {...childRoute} />
            </ListItem>
          ))}
        </UnorderedList>
      ) : null}
    </>
  );
};

/**
 * Similar to NavSideBar, but without hooks so that it is easier to test
 */
export const UnconnectedNavSideBar = ({
  routerPathname,
  ...nav
}: {
  groups: NavGroup[];
  active: ActiveNav | undefined;
  routerPathname: string;
}) => {
  // Don't render the sidebar if no group is active
  if (!nav.active) {
    return null;
  }

  return (
    <VStack as="nav" align="left" spacing={4} width="200px">
      <Heading size="md">{nav.active.title}</Heading>
      <NavList>
        {nav.active.children.map((childRoute) => (
          <NavListItem
            key={childRoute.title}
            routerPathname={routerPathname}
            {...childRoute}
          />
        ))}
      </NavList>
    </VStack>
  );
};

export const NavSideBar = () => {
  const router = useRouter();
  const nav = useNav({ path: router.pathname });

  return <UnconnectedNavSideBar routerPathname={router.pathname} {...nav} />;
};
