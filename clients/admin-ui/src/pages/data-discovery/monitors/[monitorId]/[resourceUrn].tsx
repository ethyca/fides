import { Box, Heading } from "@fidesui/react";
import { NextPage } from "next";
import { useRouter } from "next/router";
import FixedLayout from "~/features/common/FixedLayout";
import TestMonitorResultTable from "~/features/data-discovery-and-detection/TestMonitorResultTable";
import useDiscoveryRoutes from "~/features/data-discovery-and-detection/hooks/useDiscoveryRoutes";

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
      <Box display="flex" justifyContent="space-between">
        <Heading mb={8} fontSize="2xl" fontWeight="semibold">
          Data Discovery Monitor: {monitorId} {">"} {resourceUrn}
        </Heading>
      </Box>

      <TestMonitorResultTable
        monitorId={monitorId}
        resourceUrn={resourceUrn}
        onSelectResource={navigateToResourceDetails}
      />
    </FixedLayout>
  );
};
export default MonitorUrnDetailPage;
