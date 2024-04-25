import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DETECTION_DISCOVERY_ACTIVITY_ROUTE } from "~/features/common/nav/v2/routes";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import ActivityTable from "~/features/data-discovery-and-detection/tables/ActivityTable";

const DataDiscoveryAndDetectionActivityPage = () => (
  <FixedLayout
    title="Data discovery"
    mainProps={{
      padding: "40px",
      paddingRight: "48px",
    }}
  >
    <DiscoveryMonitorBreadcrumbs
      parentLink={DETECTION_DISCOVERY_ACTIVITY_ROUTE}
      parentTitle="Detection & discovery"
    />

    {/* TODO: Replace table with table that displays activity results */}
    <ActivityTable />
  </FixedLayout>
);

export default DataDiscoveryAndDetectionActivityPage;
