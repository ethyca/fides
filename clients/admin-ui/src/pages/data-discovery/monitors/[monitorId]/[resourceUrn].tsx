import { Box, Heading } from "@fidesui/react";
import { NextPage } from "next";

import FixedLayout from "~/features/common/FixedLayout";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";
import TestMonitorResultTable from "~/features/data-discovery-and-detection/TestMonitorResultTable";

const MonitorUrnDetailPage: NextPage = () => {
  const { monitorId, resourceUrn, navigateToResourceDetails } =
    useDiscoveryRoutes();

  return (
    <FixedLayout
      title="Data Discovery Monitor Detail"
      mainProps={{
        padding: "40px",
        paddingRight: "48px",
      }}
    >
      <DiscoveryMonitorBreadcrumbs
        monitorId={monitorId}
        resourceUrn={resourceUrn}
      />

      <TestMonitorResultTable
        monitorId={monitorId}
        resourceUrn={resourceUrn}
        onSelectResource={navigateToResourceDetails}
      />
    </FixedLayout>
  );
};
export default MonitorUrnDetailPage;
