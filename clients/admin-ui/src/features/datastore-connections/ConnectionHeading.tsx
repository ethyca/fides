import { Button, Flex, Heading, Spacer } from "@fidesui/react";
import React from "react";

const ConnectionStatusBadge: React.FC = () => (
  <Flex mb="24px" justifyContent="center" alignItems="center">
    <Heading fontSize="2xl" fontWeight="semibold">
      Datastore Connection Management
    </Heading>
    <Spacer />
    <Button
      variant="solid"
      bg="primary.800"
      _hover={{ bg: "primary.800" }}
      color="white"
      flexShrink={0}
      size="sm"
      disabled
    >
      Create New Connection
    </Button>
  </Flex>
);

export default ConnectionStatusBadge;
