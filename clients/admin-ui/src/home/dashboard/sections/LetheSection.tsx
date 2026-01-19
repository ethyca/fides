import { Box, Heading, SimpleGrid, Stack, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { StatCard } from "../components/StatCard";
import { useLetheData } from "../hooks/useDashboardData";

/**
 * Lethe Section Component
 * Displays Data Subject Requests (DSRs) insights
 */
export const LetheSection = () => {
  const { data, isLoading } = useLetheData();

  if (isLoading) {
    return (
      <Stack spacing={6}>
        <Box>
          <Heading as="h2" size="lg" mb={2} color={palette.FIDESUI_MINOS}>
            Lethe
          </Heading>
          <Text fontSize="sm" color={palette.FIDESUI_NEUTRAL_700} mb={4}>
            Data Subject Requests (DSRs)
          </Text>
        </Box>
        <Text>Loading...</Text>
      </Stack>
    );
  }

  return (
    <Stack spacing={6}>
      <Box>
        <Heading as="h2" size="lg" mb={2} color={palette.FIDESUI_MINOS}>
          Lethe
        </Heading>
        <Text fontSize="sm" color={palette.FIDESUI_NEUTRAL_700} mb={4}>
          Data Subject Requests (DSRs)
        </Text>
      </Box>

      <SimpleGrid columns={{ base: 1, md: 2 }} spacing={4}>
        <StatCard
          label="Privacy Requests Needing Approval"
          value={data.privacyRequestsNeedingApproval}
          color={palette.FIDESUI_WARNING}
        />
        <StatCard
          label="Pending Manual Tasks"
          value={data.pendingManualTasks}
          color={palette.FIDESUI_INFO}
        />
      </SimpleGrid>
    </Stack>
  );
};

