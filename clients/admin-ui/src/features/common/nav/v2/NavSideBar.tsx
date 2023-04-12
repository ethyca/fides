import { NavList } from "@fidesui/components";
import { Heading, VStack } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { useNav } from "./hooks";
import { NavSideBarLink } from "./NavLink";

export const NavSideBar = () => {
  const router = useRouter();
  const nav = useNav({ path: router.pathname });

  // Don't render the sidebar if no group is active
  if (!nav.active) {
    return null;
  }

  return (
    <VStack as="nav" align="left" spacing={4} width="200px">
      <Heading size="md">{nav.active.title}</Heading>
      <NavList>
        {nav.active.children.map(({ title, path }) => {
          const isActive = router.pathname.startsWith(path);

          return (
            <NavSideBarLink key={title} href={path} isActive={isActive}>
              {title}
            </NavSideBarLink>
          );
        })}
      </NavList>
    </VStack>
  );
};
