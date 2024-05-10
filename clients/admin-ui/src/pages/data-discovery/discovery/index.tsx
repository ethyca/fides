import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DISCOVERY_ROUTE } from "~/features/common/nav/v2/routes";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DiscoveryResultTable from "~/features/data-discovery-and-detection/tables/DiscoveryResultTable";

const DataDiscoveryActivityPage = () => (
  <FixedLayout
    title="Data discovery"
    mainProps={{
      padding: "40px",
      paddingRight: "48px",
    }}
  >
    <DiscoveryMonitorBreadcrumbs
      parentTitle="Data discovery"
      parentLink={DATA_DISCOVERY_ROUTE}
    />

    <DiscoveryResultTable />
  </FixedLayout>
);

export default DataDiscoveryActivityPage;
