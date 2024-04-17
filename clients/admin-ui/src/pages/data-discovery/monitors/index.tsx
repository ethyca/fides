import { Box, Heading } from "@fidesui/react";
import React from "react";
import FixedLayout from "~/features/common/FixedLayout";
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
      <Box display="flex" justifyContent="space-between">
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Data Discovery
        </Heading>
      </Box>

      <TestMonitorTable
        viewMonitorResults={(monitor) =>
          navigateToMonitorDetails({ monitorId: monitor.id! })
        }
      />
    </FixedLayout>
  );
};

export default DataDiscoveryMonitorsPage;
