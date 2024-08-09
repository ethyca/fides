import { Heading } from "fidesui";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DETECTION_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DetectionResultTable from "~/features/data-discovery-and-detection/tables/DetectionResultTable";

const DataDetectionActivityPage = () => (
  <FixedLayout
    title="Data detection"
    mainProps={{
      padding: "20px 40px 48px",
    }}
  >
    <PageHeader breadcrumbs={false}>
      <Heading>Data detection</Heading>
    </PageHeader>
    <DiscoveryMonitorBreadcrumbs parentLink={DATA_DETECTION_ROUTE} />
    <DetectionResultTable />
  </FixedLayout>
);

export default DataDetectionActivityPage;
