import { NavList } from "@fidesui/components";
import { Box, Heading, VStack } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { useNav } from "./hooks";
import { NavGroupChild } from "./nav-config";
import { NavSideBarLink } from "./NavLink";

const NavListItem = ({
  title,
  path,
  children,
  level = 0,
}: NavGroupChild & { level?: number }) => {
  const router = useRouter();
  const isActive = router.pathname.startsWith(path);

  return (
    <Box pl={3 * level}>
      <NavSideBarLink href={path} isActive={isActive}>
        {title}
      </NavSideBarLink>
      {children.map((childRoute) => (
        <NavListItem key={childRoute.title} {...childRoute} level={level + 1} />
      ))}
    </Box>
  );
};

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
        {nav.active.children.map((childRoute) => (
          <NavListItem key={childRoute.title} {...childRoute} level={0} />
        ))}
      </NavList>
    </VStack>
  );
};
