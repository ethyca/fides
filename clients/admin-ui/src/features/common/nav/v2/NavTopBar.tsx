import { Flex } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { resolveZoneLink } from "~/features/common/nav/zone-config";

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
        // The group links to its first child's path.
        const { path } = group.children[0]!;

        // We still need to handle cross-zone links.
        const { href } = resolveZoneLink({ href: path, router });

        const isActive = group.title === nav.active?.title;

        return (
          <NavTopBarLink key={group.title} href={href} isActive={isActive}>
            {group.title}
          </NavTopBarLink>
        );
      })}
    </Flex>
  );
};
