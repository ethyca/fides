import { Box, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number | string;
    color: string;
  }>;
  label?: string;
}

/**
 * Custom tooltip component for Recharts with consistent styling
 */
export const CustomTooltip = ({
  active,
  payload,
  label,
}: CustomTooltipProps) => {
  if (!active || !payload || !payload.length) {
    return null;
  }

  return (
    <Box
      bg={palette.FIDESUI_FULL_WHITE}
      border="1px solid"
      borderColor={palette.FIDESUI_NEUTRAL_200}
      borderRadius="4px"
      p={2}
      boxShadow="0px 1px 2px 0px rgba(0, 0, 0, 0.06), 0px 1px 3px 0px rgba(0, 0, 0, 0.1)"
    >
      <Text fontSize="sm" fontWeight="semibold" mb={1}>
        {label}
      </Text>
      {payload.map((entry, index) => (
        <Text key={index} fontSize="sm" color={entry.color}>
          {`${entry.name}: ${entry.value}`}
        </Text>
      ))}
    </Box>
  );
};

