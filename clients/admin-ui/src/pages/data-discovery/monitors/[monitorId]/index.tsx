import { NextPage } from "next";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DiscoveryMonitorResultTable from "~/features/data-discovery-and-detection/DiscoveryMonitorResultTable";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";

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
      <DiscoveryMonitorResultTable
        monitorId={monitorId}
        onSelectResource={navigateToResourceDetails}
      />
    </FixedLayout>
  );
};

export default DataDiscoveryMonitorDetailPage;
