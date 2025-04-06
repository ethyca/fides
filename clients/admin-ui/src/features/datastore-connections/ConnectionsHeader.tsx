import { Box, Link, Text } from "fidesui";
import React from "react";

import { useFeatures } from "~/features/common/features";

import { ADD_SYSTEMS_ROUTE } from "../common/nav/routes";
import PageHeader from "../common/PageHeader";
import AddConnectionButton from "./add-connection/AddConnectionButton";

const ConnectionsHeader = () => {
  const features = useFeatures();

  return (
    <PageHeader
      heading="Unlinked Connections"
      rightContent={
        features.flags.standaloneConnections && <AddConnectionButton />
      }
    >
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
    </PageHeader>
  );
};

export default ConnectionsHeader;
