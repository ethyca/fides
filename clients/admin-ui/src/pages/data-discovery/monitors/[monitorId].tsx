import { Box, Heading } from "@fidesui/react";
import { NextPage } from "next";
import { useRouter } from "next/router";
import React, { useEffect } from "react";
import FixedLayout from "~/features/common/FixedLayout";
import TestMonitorResultTable from "~/features/data-discovery-and-detection/TestMonitorResultTable";

const DataDiscoveryMonitorDetailPage: NextPage = () => {
  const router = useRouter();
  const monitorId = router.query.monitorId as string;

  // Data fetching
  // const { isLoading, discoveryMonitorItems } = useDiscoveryMonitorItems({
  //   urn,
  // });

  // Actions
  // const { mute, accept, reject, monitor } = useDiscoveryMonitorActions();

  return (
    <FixedLayout
      title="Data Discovery Monitor Detail"
      mainProps={{
        padding: "40px",
        paddingRight: "48px",
      }}
    >
      <Box display="flex" justifyContent="space-between">
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Data Discovery Monitor: {monitorId}
        </Heading>
      </Box>
      {/* <DiscoveryMonitorBreadcrumbs urn={urn} />
      <DiscoveryMonitorItemsTable
        discoveryMonitorItems={discoveryMonitorItems}
        onAccept={accept}
        onMute={mute}
        onReject={reject}
        onMonitor={monitor}
        onNavigate={navigateToUrn}
      /> */}

      <TestMonitorResultTable configId={monitorId} />
    </FixedLayout>
  );
};

export default DataDiscoveryMonitorDetailPage;
