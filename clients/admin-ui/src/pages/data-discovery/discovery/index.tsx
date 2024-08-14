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
    <PageHeader
      breadcrumbs={[{ title: "Data discovery" }, { title: "All activity" }]}
    />
    <DiscoveryResultTable />
  </FixedLayout>
);

export default DataDiscoveryActivityPage;
