import { Flex, List, Typography } from "fidesui";

import { MockConnection, SystemLink } from "~/mocks/system-links/data";

const IntegrationLinkedSystems = ({
  connection,
}: {
  connection: MockConnection & { linked_systems: SystemLink[] };
}) => {
  return (
    <Flex vertical gap={2}>
      <Typography.Title level={5}>Linked systems</Typography.Title>
      <List>
        {connection.linked_systems?.map((system) => (
          <List.Item key={system.system_fides_key}>
            {system.system_name}
          </List.Item>
        ))}
      </List>
    </Flex>
  );
};

export default IntegrationLinkedSystems;
