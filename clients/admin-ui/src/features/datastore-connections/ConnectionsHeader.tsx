import { Box, Flex, Heading, Link, Spacer, Text } from "fidesui";
import React from "react";

import { useFeatures } from "~/features/common/features";

import { ADD_SYSTEMS_ROUTE } from "../common/nav/v2/routes";
import AddConnectionButton from "./add-connection/AddConnectionButton";

const ConnectionsHeader = () => {
  const features = useFeatures();

  return (
    <Flex
      mb="24px"
      flexDirection="column"
      justifyContent="center"
      alignItems="left"
    >
      <Flex>
        <Heading marginBottom={4} fontSize="2xl" fontWeight="semibold">
          Unlinked Connections
        </Heading>
        <Spacer />
        {features.flags.standaloneConnections && <AddConnectionButton />}
      </Flex>
      <Box maxWidth="450px">
        <Text fontSize="sm">
          Connections are now created in the{" "}
          <Link color="complimentary.500" href={ADD_SYSTEMS_ROUTE}>
            system configuration
          </Link>{" "}
          section. You can link existing connections to a new or existing
          system.
        </Text>
      </Box>
    </Flex>
  );
};

export default ConnectionsHeader;
