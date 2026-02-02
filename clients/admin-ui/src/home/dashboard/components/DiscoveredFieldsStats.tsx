import { Box, SimpleGrid, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import type { FieldStatusData } from "../types";

interface DiscoveredFieldsStatsProps {
  total: number;
  breakdown: FieldStatusData[];
}

/**
 * Component displaying discovered fields statistics with breakdown
 */
export const DiscoveredFieldsStats = ({
  total,
  breakdown,
}: DiscoveredFieldsStatsProps) => (
  <Box
    bg={palette.FIDESUI_CORINTH}
    borderRadius="6px"
    p={6}
    border="1px solid"
    borderColor={palette.FIDESUI_NEUTRAL_100}
  >
    <Text
      fontSize="sm"
      color={palette.FIDESUI_NEUTRAL_700}
      mb={4}
      fontWeight="medium"
    >
      Discovered Fields Overview
    </Text>

    {/* Total */}
    <Box mb={6}>
      <Text
        fontSize="xs"
        color={palette.FIDESUI_NEUTRAL_700}
        mb={1}
        textTransform="uppercase"
        letterSpacing="0.5px"
      >
        Total Discovered Fields
      </Text>
      <Text fontSize="4xl" fontWeight="bold" color={palette.FIDESUI_MINOS}>
        {total.toLocaleString()}
      </Text>
    </Box>

    {/* Breakdown grid */}
    <SimpleGrid columns={2} spacing={4}>
      {breakdown.map((item) => (
        <Box key={item.name}>
          <Text
            fontSize="xs"
            color={palette.FIDESUI_NEUTRAL_700}
            mb={1}
            textTransform="uppercase"
            letterSpacing="0.5px"
          >
            {item.name}
          </Text>
          <Text fontSize="2xl" fontWeight="bold" color={item.color}>
            {item.value.toLocaleString()}
          </Text>
        </Box>
      ))}
    </SimpleGrid>
  </Box>
);

