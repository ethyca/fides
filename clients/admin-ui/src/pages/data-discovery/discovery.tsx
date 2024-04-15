import React from "react";
import FixedLayout from "~/features/common/FixedLayout";
import DiscoveryMonitorBreadcrumbs from "~/features/data-discovery-and-detection/DiscoveryMonitorBreadcrumbs";
import DiscoveryMonitorItemsTable from "~/features/data-discovery-and-detection/DiscoveryMonitorItemsTable";
import useDiscoveryMonitorActions from "~/features/data-discovery-and-detection/hooks/useDiscoveryMonitorActions";
import useDiscoveryMonitorItems from "~/features/data-discovery-and-detection/hooks/useDiscoveryMonitorItems";
import useUrnPaths from "~/features/data-discovery-and-detection/hooks/useUrnPaths";
import TestDiscoveryPage from "~/features/data-discovery-and-detection/TestDiscoveryTable";

const DataDiscoveryPage = () => {
  // const { urn, navigateToUrn } = useUrnPaths();
  // // Data fetching
  // const { isLoading, discoveryMonitorItems } = useDiscoveryMonitorItems({
  //   urn,
  // });
  // // Actions
  // const { mute, accept, reject, monitor } = useDiscoveryMonitorActions();
  // return (
  //   <FixedLayout
  //     title="Data discovery "
  //     mainProps={{
  //       padding: "40px",
  //       paddingRight: "48px",
  //     }}
  //   >
  //     <DiscoveryMonitorBreadcrumbs urn={urn} />
  //     <DiscoveryMonitorItemsTable
  //       discoveryMonitorItems={discoveryMonitorItems}
  //       onAccept={accept}
  //       onMute={mute}
  //       onReject={reject}
  //       onMonitor={monitor}
  //       onNavigate={navigateToUrn}
  //     />
  //   </FixedLayout>
  // );
  return <TestDiscoveryPage />;
};

export default DataDiscoveryPage;
