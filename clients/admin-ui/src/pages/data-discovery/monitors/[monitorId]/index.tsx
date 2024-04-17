import { NextPage } from "next";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import TestMonitorResultTable from "~/features/data-discovery-and-detection/TestMonitorResultTable";

const DataDiscoveryMonitorDetailPage: NextPage = () => {
  const { navigateToResourceDetails, monitorId } = useDiscoveryRoutes();

  return (
    <FixedLayout
      title="Data Discovery Monitor Detail"
      mainProps={{
        padding: "40px",
        paddingRight: "48px",
      }}
    >
      <DiscoveryMonitorBreadcrumbs monitorId={monitorId} />
      <TestMonitorResultTable
        monitorId={monitorId}
        onSelectResource={navigateToResourceDetails}
      />
    </FixedLayout>
  );
};

export default DataDiscoveryMonitorDetailPage;
