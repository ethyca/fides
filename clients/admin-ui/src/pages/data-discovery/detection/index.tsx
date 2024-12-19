import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DETECTION_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DetectionResultTable from "~/features/data-discovery-and-detection/tables/DetectionResultTable";

const DataDetectionActivityPage = () => (
  <FixedLayout title="Data detection">
    <PageHeader heading="Data detection">
      <DiscoveryMonitorBreadcrumbs parentLink={DATA_DETECTION_ROUTE} />
    </PageHeader>

    <DetectionResultTable />
  </FixedLayout>
);

export default DataDetectionActivityPage;
