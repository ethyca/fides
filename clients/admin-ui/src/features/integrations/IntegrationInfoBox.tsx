import { Flex } from "@fidesui/react";

import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import { ConnectionSystemTypeMap } from "~/types/api";

const IntegrationInfoBox = ({ data }: { data: ConnectionSystemTypeMap }) => (
  <Flex>
    <ConnectionTypeLogo data={data} w="90px" h="90px" />
  </Flex>
);

export default IntegrationInfoBox;
