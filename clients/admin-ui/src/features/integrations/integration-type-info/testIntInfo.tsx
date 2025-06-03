import { ConnectionCategory } from "~/features/integrations/ConnectionCategory";
import { AccessLevel, ConnectionType } from "~/types/api";

export const TEST_CONNECTOR_TYPE_INFO = {
  placeholder: {
    name: "Test Connector",
    key: "test_connector",
    connection_type: ConnectionType.TEST_CONNECTOR,
    access: AccessLevel.READ,
    created_at: "",
  },
  category: ConnectionCategory.DATA_WAREHOUSE,
  tags: [],
  overview: <>overview</>,
  instructions: <>instructions</>,
};
