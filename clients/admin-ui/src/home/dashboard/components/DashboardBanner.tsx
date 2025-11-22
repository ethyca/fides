import { Flex, Text } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import * as React from "react";

import { useFeatures } from "~/features/common/features";

/**
 * Dashboard Banner Component
 * Displays a welcome message based on whether the user has systems configured
 */
export const DashboardBanner = () => {
  const { systemsCount } = useFeatures();
  const hasSystems = systemsCount > 0;

  return (
    <Flex
      background={palette.FIDESUI_CORINTH}
      p={6}
      marginX={-10}
      marginY={-10}
      mb={4}
    >
      <Flex flexDir="column" maxWidth="600px">
        {hasSystems && (
          <Text fontSize="3xl" fontWeight="semibold" color={palette.FIDESUI_MINOS}>
            Welcome back!
          </Text>
        )}
        {!hasSystems && (
          <Text fontSize="3xl" fontWeight="semibold" color={palette.FIDESUI_MINOS}>
            Welcome to Fides!
          </Text>
        )}
      </Flex>
    </Flex>
  );
};
