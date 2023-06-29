import { Flex } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { useNav } from "./hooks";
import { NavTopBarLink } from "./NavLink";

export const NavTopBar = () => {
  const router = useRouter();
  const nav = useNav({ path: router.pathname });

  return (
    <Flex
      as="nav"
      height={12}
      paddingX={10}
      gap={1}
      flexShrink={0}
      alignItems="center"
      borderBottom="1px"
      borderColor="gray.100"
    >
      {nav.groups.map((group) => {
        // "Management" is navigated to via the gear icon, so don't display it in the nav
        if (group.title === "Management") {
          return null;
        }
        // The group links to its first child's path.
        const { path } = group.children[0]!;

        const isActive = group.title === nav.active?.title;

        return (
          <NavTopBarLink key={group.title} href={path} isActive={isActive}>
            {group.title}
          </NavTopBarLink>
        );
      })}
    </Flex>
  );
};
