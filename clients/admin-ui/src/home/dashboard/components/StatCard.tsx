import { Box, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

interface StatCardProps {
  label: string;
  value: number | string;
  color?: string;
  size?: "sm" | "md" | "lg";
}

/**
 * Reusable stat card component for displaying metrics
 */
export const StatCard = ({
  label,
  value,
  color = palette.FIDESUI_MINOS,
  size = "md",
}: StatCardProps) => {
  const fontSizeMap = {
    sm: "2xl",
    md: "3xl",
    lg: "4xl",
  } as const;

  return (
    <Box
      bg={palette.FIDESUI_CORINTH}
      borderRadius="6px"
      p={6}
      border="1px solid"
      borderColor={palette.FIDESUI_NEUTRAL_100}
    >
      <Text fontSize="sm" color={palette.FIDESUI_NEUTRAL_700} mb={2}>
        {label}
      </Text>
      <Text
        fontSize={fontSizeMap[size]}
        fontWeight="bold"
        color={color}
      >
        {typeof value === "number" ? value.toLocaleString() : value}
      </Text>
    </Box>
  );
};

