import { Box, Flex, Heading, Link, SimpleGrid } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { DataClassificationTreemapCard } from "../components/DataClassificationTreemapCard";
import { SystemDetectionIcon } from "../components/icons/SystemDetectionIcon";
import { dummyDashboardData } from "../data/dummyData";

/**
 * Data Classification section component
 * Displays treemap cards for different systems showing data category breakdowns
 */
export const DataClassificationSection = () => {
  const { dataClassification } = dummyDashboardData;

  return (
    <Box mb={10}>
      {/* Header */}
      <Flex
        alignItems="center"
        justifyContent="space-between"
        mb={4}
        flexWrap="wrap"
        gap={4}
      >
        <Flex alignItems="center" gap={2}>
          <Box display="flex" alignItems="center" gap={0.5}>
            <SystemDetectionIcon width="26px" height="20px" color={palette.FIDESUI_MINOS} />
          </Box>
          <Heading as="h2" size="md" color={palette.FIDESUI_MINOS}>
            Data Classification
          </Heading>
        </Flex>
        <Flex alignItems="center" gap={2}>
          <Link
            href="/action-center"
            fontSize="sm"
            color={palette.FIDESUI_LINK}
            _hover={{ textDecoration: "underline" }}
          >
            View All
          </Link>
        </Flex>
      </Flex>

      {/* Data Classification Treemap Cards */}
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        {dataClassification.systems.map((system, index) => (
          <DataClassificationTreemapCard
            key={`${system.systemName}-${index}`}
            systemName={system.systemName}
            data={system.categories}
            height={300}
          />
        ))}
      </SimpleGrid>
    </Box>
  );
};

