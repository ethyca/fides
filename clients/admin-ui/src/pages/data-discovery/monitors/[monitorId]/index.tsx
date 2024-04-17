import React from "react";
import { Box, Heading } from "@fidesui/react";
import { NextPage } from "next";
import { useRouter } from "next/router";
import FixedLayout from "~/features/common/FixedLayout";
import TestMonitorResultTable from "~/features/data-discovery-and-detection/TestMonitorResultTable";
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
      <Box display="flex" justifyContent="space-between">
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Data Discovery Monitor: {monitorId}
        </Heading>
      </Box>

      <TestMonitorResultTable
        monitorId={monitorId}
        onSelectResource={navigateToResourceDetails}
      />
    </FixedLayout>
  );
};

export default DataDiscoveryMonitorDetailPage;
