import { Box, Heading, Text } from "@fidesui/react";

import BorderGrid from "~/features/common/BorderGrid";
import { System } from "~/types/api";

interface SystemBoxProps {
  system: System;
}
const SystemBox = ({ system }: SystemBoxProps) => (
  <Box p={4} data-testid={`system-${system.fides_key}`}>
    <Heading as="h2" fontSize="16px" mb={2}>
      {system.name}
    </Heading>
    <Box color="gray.600" fontSize="14px">
      <Text>{system.description}</Text>
      <Text>{system.fides_key}</Text>
    </Box>
  </Box>
);

interface Props {
  systems: System[] | undefined;
}
const SystemsGrid = ({ systems }: Props) => {
  if (!systems || !systems.length) {
    return <div data-testid="empty-state">Empty state</div>;
  }

  return (
    <BorderGrid<System>
      columns={3}
      items={systems}
      renderItem={(system) => <SystemBox system={system} />}
    />
  );
};

export default SystemsGrid;
