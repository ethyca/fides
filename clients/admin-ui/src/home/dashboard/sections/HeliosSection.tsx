import { Box, Heading, SimpleGrid, Stack, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { ClassificationActivityChart } from "../components/charts/ClassificationActivityChart";
import { DataCategoriesTreemap } from "../components/charts/DataCategoriesTreemap";
import { FieldStatusPieChart } from "../components/charts/FieldStatusPieChart";
import { DiscoveredFieldsStats } from "../components/DiscoveredFieldsStats";
import { useHeliosData } from "../hooks/useDashboardData";
import type { HeliosData } from "../types";

/**
 * Helios Section Component
 * Displays data detection and classification insights
 */
export const HeliosSection = () => {
  const { data, isLoading } = useHeliosData();

  // Calculate total from discovered fields
  const totalDiscoveredFields = React.useMemo(
    () =>
      data.discoveredFields.reduce((sum, item) => sum + item.value, 0),
    [data.discoveredFields]
  );

  if (isLoading) {
    return (
      <Stack spacing={6}>
        <Box>
          <Heading as="h2" size="lg" mb={2} color={palette.FIDESUI_MINOS}>
            Helios
          </Heading>
          <Text fontSize="sm" color={palette.FIDESUI_NEUTRAL_700} mb={4}>
            Data Detection and Classification
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
          Helios
        </Heading>
        <Text fontSize="sm" color={palette.FIDESUI_NEUTRAL_700} mb={4}>
          Data Detection and Classification
        </Text>
      </Box>

      {/* Discovered fields stats and pie chart in grid */}
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={6}>
        <DiscoveredFieldsStats
          total={totalDiscoveredFields}
          breakdown={data.discoveredFields}
        />
        <FieldStatusPieChart data={data.discoveredFields} />
      </SimpleGrid>

      {/* Classification activity over time */}
      <ClassificationActivityChart data={data.classificationActivity} />

      {/* Data categories treemap */}
      <DataCategoriesTreemap data={data.dataCategories} />
    </Stack>
  );
};

