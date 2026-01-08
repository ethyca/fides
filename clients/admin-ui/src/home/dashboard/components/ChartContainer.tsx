import { Box, Heading } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

interface ChartContainerProps {
  title: string;
  children: React.ReactNode;
  height?: number;
}

/**
 * Reusable container component for charts with consistent styling
 */
export const ChartContainer = ({
  title,
  children,
  height = 300,
}: ChartContainerProps) => (
  <Box
    bg={palette.FIDESUI_CORINTH}
    borderRadius="6px"
    p={4}
    border="1px solid"
    borderColor={palette.FIDESUI_NEUTRAL_100}
  >
    <Heading as="h4" size="sm" mb={4} color={palette.FIDESUI_MINOS}>
      {title}
    </Heading>
    <Box
      height={`${height}px`}
      width="100%"
      minWidth={0}
      minHeight={0}
      position="relative"
    >
      {children}
    </Box>
  </Box>
);

