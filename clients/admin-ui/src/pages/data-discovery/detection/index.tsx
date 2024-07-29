import { Heading } from "fidesui";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DetectionResultTable from "~/features/data-discovery-and-detection/tables/DetectionResultTable";

const DataDetectionActivityPage = () => (
  <FixedLayout
    title="Data detection"
    mainProps={{
      padding: "0 40px 48px",
    }}
  >
    <PageHeader breadcrumbs={false}>
      <Heading fontSize="2xl" fontWeight={600}>
        Data detection
      </Heading>
    </PageHeader>
    {/* TEMPORARY HACK */}
    <DiscoveryMonitorBreadcrumbs parentTitle="All activity" parentLink="/" />
    <DetectionResultTable />
  </FixedLayout>
);

export default DataDetectionActivityPage;
