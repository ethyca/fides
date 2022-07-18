import { Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";

import { System } from "~/types/api";

interface Props {
  systems: System[] | undefined;
}
const SystemsTable = ({ systems }: Props) => {
  if (!systems || !systems.length) {
    return <div data-testid="empty-state">Empty state</div>;
  }
  return (
    <Table size="sm" data-testid="systems-table">
      <Thead>
        <Tr>
          <Th>Name</Th>
          <Th>Description</Th>
        </Tr>
      </Thead>
      <Tbody>
        {systems.map((system) => (
          <Tr key={system.fides_key} data-testid="systems-row">
            <Td>{system.name}</Td>
            <Td>{system.description}</Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default SystemsTable;
