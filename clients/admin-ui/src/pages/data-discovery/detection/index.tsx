import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DETECTION_ROUTE } from "~/features/common/nav/v2/routes";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DetectionResultTable from "~/features/data-discovery-and-detection/tables/DetectionResultTable";

const DataDetectionActivityPage = () => (
  <FixedLayout
    title="Data detection"
    mainProps={{
      padding: "20px 40px 48px",
    }}
  >
    <DiscoveryMonitorBreadcrumbs
      parentTitle="Data detection"
      parentLink={DATA_DETECTION_ROUTE}
    />
    <DetectionResultTable />
  </FixedLayout>
);

export default DataDetectionActivityPage;
