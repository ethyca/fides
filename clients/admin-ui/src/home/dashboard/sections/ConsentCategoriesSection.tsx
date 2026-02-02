import { Box, Flex, Heading, Icons, Link, Select, SimpleGrid, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { ConsentCategoryCard } from "../components/ConsentCategoryCard";
import { ConsentIcon } from "../components/icons/ConsentIcon";
import { dummyDashboardData } from "../data/dummyData";

/**
 * Consent categories section component
 * Displays consent category cards with trend indicators
 */
export const ConsentCategoriesSection = () => {
  const { consentCategories } = dummyDashboardData;
  const [timeRange, setTimeRange] = React.useState(consentCategories.timeRange);

  return (
    <Box>
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
            <ConsentIcon width="26px" height="20px" color={palette.FIDESUI_MINOS} />
          </Box>
          <Heading as="h2" size="md" color={palette.FIDESUI_MINOS}>
            Consent
          </Heading>
        </Flex>
        <Flex alignItems="center" gap={2}>
          <Link
            href="/consent"
            fontSize="sm"
            color={palette.FIDESUI_LINK}
            _hover={{ textDecoration: "underline" }}
          >
            View All
          </Link>
        </Flex>
      </Flex>

      {/* Consent Category Cards */}
      <SimpleGrid columns={{ base: 1, sm: 2, md: 3, lg: 5 }} spacing={4}>
        {consentCategories.categories.map((category, index) => (
          <ConsentCategoryCard
            key={`${category.category}-${index}`}
            category={category.category}
            value={category.value}
            change={category.change}
            trendData={category.trendData}
          />
        ))}
      </SimpleGrid>
    </Box>
  );
};
