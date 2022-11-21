import { Flex } from "@fidesui/react";
import dynamic from "next/dynamic";
import React from "react";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { Flags } from "react-feature-flags";

import {
  DATASTORE_CONNECTION_ROUTE,
  INDEX_ROUTE,
  USER_MANAGEMENT_ROUTE,
} from "~/constants";
import { useFeatures } from "~/features/common/features.slice";

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
        <NavLink title="Privacy Requests" href={INDEX_ROUTE} exact />
        <NavLink title="Connections" href={DATASTORE_CONNECTION_ROUTE} />
        <NavLink title="User Management" href={USER_MANAGEMENT_ROUTE} />
        <NavLink title="Systems" href="/system" />
        <NavLink title="Datasets" href="/dataset" />

        {/* Links under the datamap zone: */}
        {features.plus ? <NavLink title="Data Map" href="/datamap" /> : null}

        <NavLink title="Taxonomy" href="/taxonomy" />
        <NavLink title="Config Wizard" href="/config-wizard" />
      </nav>
    </Flex>
  );
};

export default NavBar;
