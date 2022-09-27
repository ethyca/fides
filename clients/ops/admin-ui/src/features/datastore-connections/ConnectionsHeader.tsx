import { Flex, Heading, Spacer } from "@fidesui/react";
import React from "react";

import AddConnectionButton from "./add-connection/AddConnectionButton";

type ConnectionsHeaderProps = {
  hasConnections: boolean;
};

const ConnectionsHeader: React.FC<ConnectionsHeaderProps> = ({
  hasConnections = false,
}) => (
  <Flex mb="24px" justifyContent="center" alignItems="center">
    <Heading fontSize="2xl" fontWeight="semibold">
      Datastore Connection Management
    </Heading>
    <Spacer />
    {hasConnections && <AddConnectionButton />}
  </Flex>
);

export default ConnectionsHeader;
