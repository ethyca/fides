import { AntTypography as Typography, Box, Flex, SimpleGrid, Text } from "fidesui";
import { Icons } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

interface SummaryBreakdownItem {
  label: string;
  value: number;
  color?: string;
}

interface SummaryCardProps {
  title: string;
  icon: React.ReactElement;
  total: number;
  totalLabel: string;
  breakdown: SummaryBreakdownItem[];
  viewAllHref?: string;
  leftBorderColor?: string; // Color for the 9px left border
}

/**
 * Summary card component for dashboard top section
 * Displays a main metric with breakdown and optional "View All" link
 * Matches the design specification exactly
 */
export const SummaryCard = ({
  title,
  icon,
  total,
  totalLabel,
  breakdown,
  viewAllHref,
  leftBorderColor,
}: SummaryCardProps) => (
  <Box
    position="relative"
    borderRadius="6px"
    border="1px solid"
    borderColor={palette.FIDESUI_NEUTRAL_200}
    height="100%"
    overflow="hidden"
    bg={palette.FIDESUI_NEUTRAL_50}
  >
    {/* Colored left border */}
    {leftBorderColor && (
      <Box
        position="absolute"
        left={0}
        top={0}
        bottom={0}
        width="9px"
        bg={leftBorderColor}
        zIndex={1}
      />
    )}
    <Box
      pl={leftBorderColor ? "9px" : 0}
      height="100%"
      display="flex"
      flexDirection="column"
    >
      {/* Header with View All on the right */}
      <Box p={4} pb={0}>
        <Flex alignItems="center" justifyContent="space-between" mb={4}>
          <Flex alignItems="center" gap={2}>
            <Box color={palette.FIDESUI_MINOS}>{icon}</Box>
            <Typography.Title
              level={3}
              style={{
                margin: 0,
                fontSize: "16px",
                fontWeight: 700,
                lineHeight: "24px",
                color: palette.FIDESUI_MINOS
              }}
            >
              {title}
            </Typography.Title>
          </Flex>
          {viewAllHref && (
            <Typography.Link
              href={viewAllHref}
              style={{ fontSize: "14px", color: palette.FIDESUI_INFO }}
            >
              View All
            </Typography.Link>
          )}
        </Flex>

        {/* Total */}
        <Box mb={4}>
          <Text fontSize="24px" fontWeight="bold" color={palette.FIDESUI_MINOS} lineHeight="32px">
            {total.toLocaleString()} <Text as="span" fontWeight="normal">{totalLabel}</Text>
          </Text>
        </Box>
      </Box>

      {/* Breakdown - extends to edges */}
      <SimpleGrid columns={2} spacing={0} gap={0} flex={1}>
        {breakdown.map((item, index) => (
          <Box
            key={item.label}
            borderTop={index < 2 ? "1px solid" : "none"}
            borderRight={index % 2 === 0 ? "1px solid" : "none"}
            borderBottom={index < 2 ? "1px solid" : "none"}
            borderLeft="none"
            borderColor={palette.FIDESUI_NEUTRAL_200}
            p={3}
          >
            <Text fontSize="xs" color={palette.FIDESUI_NEUTRAL_700} mb={1} fontWeight="normal">
              {item.label}
            </Text>
            <Text fontSize="xl" fontWeight="bold" color={palette.FIDESUI_MINOS}>
              {item.value.toLocaleString()}
            </Text>
          </Box>
        ))}
      </SimpleGrid>
    </Box>
  </Box>
);
