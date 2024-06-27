import { Flex, Text } from "fidesui";
import React from "react";

const ConnectionsEmptyState = () => (
  <Flex
    bg="gray.50"
    width="100%"
    height="340px"
    justifyContent="center"
    alignItems="center"
    flexDirection="column"
    data-testid="connections-empty-state"
  >
    <Text
      color="black"
      fontSize="x-large"
      lineHeight="32px"
      fontWeight="600"
      mb="7px"
    >
      All of your connections have been linked!
    </Text>
    <Text color="gray.600" fontSize="sm" lineHeight="20px" mb="11px">
      You are ready to upgrade Fides
    </Text>
  </Flex>
);

export default ConnectionsEmptyState;
