import React from "react";
import FixedLayout from "~/features/common/FixedLayout";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import TestMonitorTable from "~/features/data-discovery-and-detection/TestMonitorTable";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";

const DataDiscoveryMonitorsPage = () => {
  const { navigateToMonitorDetails } = useDiscoveryRoutes();

  return (
    <FixedLayout
      title="Data discovery"
      mainProps={{
        padding: "40px",
        paddingRight: "48px",
      }}
    >
      <DiscoveryMonitorBreadcrumbs />
      <TestMonitorTable
        viewMonitorResults={(monitor) =>
          navigateToMonitorDetails({ monitorId: monitor.id! })
        }
      />
    </FixedLayout>
  );
};

export default DataDiscoveryMonitorsPage;
