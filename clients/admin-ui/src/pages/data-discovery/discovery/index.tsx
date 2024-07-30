import { Heading } from "fidesui";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DISCOVERY_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DiscoveryResultTable from "~/features/data-discovery-and-detection/tables/DiscoveryResultTable";

const DataDiscoveryActivityPage = () => (
  <FixedLayout
    title="Data discovery"
    mainProps={{
      padding: "0 40px 48px",
    }}
  >
    <PageHeader breadcrumbs={false}>
      <Heading fontSize="2xl" fontWeight={600}>
        Data discovery
      </Heading>
    </PageHeader>
    <DiscoveryMonitorBreadcrumbs parentLink={DATA_DISCOVERY_ROUTE} />
    <DiscoveryResultTable />
  </FixedLayout>
);

export default DataDiscoveryActivityPage;
