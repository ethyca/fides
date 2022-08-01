import { Flex, Text } from "@fidesui/react";
import React from "react";

import AddConnectionButton from "./add-connection/AddConnectionButton";

const ConnectionsEmptyState: React.FC = () => (
  <Flex
    bg="gray.50"
    width="100%"
    height="340px"
    justifyContent="center"
    alignItems="center"
    flexDirection="column"
  >
    <Text
      color="black"
      fontSize="x-large"
      lineHeight="32px"
      fontWeight="600"
      mb="7px"
    >
      Welcome to your Datastores!
    </Text>
    <Text color="gray.600" fontSize="sm" lineHeight="20px" mb="11px">
      You don&lsquo;t have any Connections set up yet.
    </Text>
    <AddConnectionButton />
  </Flex>
);

export default ConnectionsEmptyState;
