import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DISCOVERY_ROUTE } from "~/features/common/nav/v2/routes";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DetectionResultTable from "~/features/data-discovery-and-detection/tables/DetectionResultTable";

const DataDetectionActivityPage = () => (
  <FixedLayout
    title="Data detection"
    mainProps={{
      padding: "40px",
      paddingRight: "48px",
    }}
  >
    <DiscoveryMonitorBreadcrumbs
      parentTitle="Data detection"
      parentLink={DATA_DISCOVERY_ROUTE}
    />

    <DetectionResultTable />
  </FixedLayout>
);

export default DataDetectionActivityPage;
