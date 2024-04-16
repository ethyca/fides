import { useRouter } from "next/router";
import React from "react";
import FixedLayout from "~/features/common/FixedLayout";
import { DATA_DISCOVERY_MONITOR_DETAIL } from "~/features/common/nav/v2/routes";
import TestMonitorTable from "~/features/data-discovery-and-detection/TestMonitorTable";

const DataDiscoveryMonitorsPage = () => {
  const router = useRouter();

  // Data fetching
  // const { isLoading, discoveryMonitorItems } = useDiscoveryMonitorItems({
  //   urn,
  // });

  // Actions
  // const { mute, accept, reject, monitor } = useDiscoveryMonitorActions();

  const navigateToMonitorDetails = (monitorId: string) => {
    router.push({
      pathname: DATA_DISCOVERY_MONITOR_DETAIL,
      query: {
        monitorId: monitorId,
      },
    });
  };

  return (
    <FixedLayout
      title="Data discovery"
      mainProps={{
        padding: "40px",
        paddingRight: "48px",
      }}
    >
      {/* <DiscoveryMonitorBreadcrumbs urn={urn} /> */}
      {/* <DiscoveryMonitorItemsTable
        discoveryMonitorItems={discoveryMonitorItems}
        onAccept={accept}
        onMute={mute}
        onReject={reject}
        onMonitor={monitor}
        onNavigate={navigateToUrn}
      /> */}
      <TestMonitorTable
        viewMonitorResults={(monitor) => navigateToMonitorDetails(monitor.id!)}
      />
    </FixedLayout>
  );
};

export default DataDiscoveryMonitorsPage;
