import { Heading } from "fidesui";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
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
    <DiscoveryResultTable />
  </FixedLayout>
);

export default DataDiscoveryActivityPage;
