import { Box, Heading, Stack, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { ConsentRatesChart } from "../components/charts/ConsentRatesChart";
import { useJanusData } from "../hooks/useDashboardData";

/**
 * Janus Section Component
 * Displays consent management insights
 */
export const JanusSection = () => {
  const { data, isLoading } = useJanusData();

  if (isLoading) {
    return (
      <Stack spacing={6}>
        <Box>
          <Heading as="h2" size="lg" mb={2} color={palette.FIDESUI_MINOS}>
            Janus
          </Heading>
          <Text fontSize="sm" color={palette.FIDESUI_NEUTRAL_700} mb={4}>
            Consent
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
          Janus
        </Heading>
        <Text fontSize="sm" color={palette.FIDESUI_NEUTRAL_700} mb={4}>
          Consent
        </Text>
      </Box>

      <ConsentRatesChart data={data.consentRates} />
    </Stack>
  );
};

