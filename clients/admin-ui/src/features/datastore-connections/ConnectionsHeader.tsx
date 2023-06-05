import { Box, Flex, Heading, Link, Text } from "@fidesui/react";
import React from "react";

import { ADD_SYSTEMS_ROUTE } from "../common/nav/v2/routes";

const ConnectionsHeader: React.FC = () => (
  <Flex
    mb="24px"
    flexDirection="column"
    justifyContent="center"
    alignItems="left"
  >
    <Heading marginBottom={4} fontSize="2xl" fontWeight="semibold">
      Unlinked Connections
    </Heading>
    <Box maxWidth="450px">
      <Text fontSize="sm">
        Connections are now created in the{" "}
        <Link color="complimentary.500" href={ADD_SYSTEMS_ROUTE}>
          system configuration
        </Link>{" "}
        section. You can link existing connections to a new or existing system.
      </Text>
    </Box>
  </Flex>
);

export default ConnectionsHeader;
