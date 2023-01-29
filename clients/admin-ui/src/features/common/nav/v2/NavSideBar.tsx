import { NavList } from "@fidesui/components";
import { Heading, VStack } from "@fidesui/react";
import { useRouter } from "next/router";
import React from "react";

import { useFeatures } from "~/features/common/features";
import { resolveZoneLink } from "~/features/common/nav/zone-config";

import { useNav } from "./hooks";
import { NavSideBarLink } from "./NavLink";

export const NavSideBar = () => {
  const router = useRouter();
  const nav = useNav({ path: router.pathname });
  const features = useFeatures();

  // Don't render the sidebar if no group is active or if the group only has one link.
  if (!nav.active || nav.active.children.length <= 1) {
    return null;
  }

  return (
    <VStack as="nav" align="left" spacing={4} width="200px">
      <Heading size="md">{nav.active.title}</Heading>
      <NavList>
        {nav.active.children.map(({ title, path }) => {
          // We still need to handle cross-zone links.
          const { href, isActive } = resolveZoneLink({ href: path, router });

          if (
            href === "/privacy-requests/configure" &&
            !features.flags.privacyRequestsConfiguration
          ) {
            return null;
          } return (
              <NavSideBarLink key={title} href={href} isActive={isActive}>
                {title}
              </NavSideBarLink>
            );
        })}
      </NavList>
    </VStack>
  );
};
