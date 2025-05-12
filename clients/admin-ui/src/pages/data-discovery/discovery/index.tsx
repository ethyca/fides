import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DISCOVERY_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DiscoveryResultTable from "~/features/data-discovery-and-detection/tables/DiscoveryResultTable";

const DataDiscoveryActivityPage = () => (
  <FixedLayout title="Data discovery">
    <PageHeader heading="Data discovery">
      <DiscoveryMonitorBreadcrumbs parentLink={DATA_DISCOVERY_ROUTE} />
    </PageHeader>
    <DiscoveryResultTable />
  </FixedLayout>
);

export default DataDiscoveryActivityPage;
