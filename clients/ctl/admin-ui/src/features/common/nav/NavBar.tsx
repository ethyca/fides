import { Flex } from "@fidesui/react";
import React from "react";

import { ArrowDownLineIcon } from "~/features/common/Icon";

import { NavLink } from "./NavLink";

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
