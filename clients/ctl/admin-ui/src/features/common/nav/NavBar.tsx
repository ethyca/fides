import { Flex } from "@fidesui/react";
import dynamic from "next/dynamic";
import React from "react";

import { useFeatures } from "~/features/common/features.slice";
import { ArrowDownLineIcon } from "~/features/common/Icon";

// Cross-zone navigation requires building URLs from the current `window.location`
// which is not available in Server-Side-Rendered components.
const NavLink = dynamic(() => import("./NavLink"), { ssr: false });

const NavBar = () => {
  const features = useFeatures();

  return (
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

        {/* Links under the datamap zone: */}
        {features.plus ? <NavLink title="Data Map" href="/datamap" /> : null}

        <NavLink title="Taxonomy" href="/taxonomy" />
        {/* This is a temporary link to the config wizard while it's still in progress */}
        <NavLink title="Config Wizard" href="/config-wizard" />
      </nav>
    </Flex>
  );
};

export default NavBar;
