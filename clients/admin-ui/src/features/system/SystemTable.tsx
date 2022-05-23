import { Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";

import { System } from "./types";

interface Props {
  systems: System[] | undefined;
}
const SystemsTable = ({ systems }: Props) => {
  if (!systems) {
    return <div>Empty state</div>;
  }
  return (
    <Table size="sm">
      <Thead>
        <Tr>
          <Th>Name</Th>
          <Th>Description</Th>
        </Tr>
      </Thead>
      <Tbody>
        {systems.map((system) => (
          <Tr key={system.fides_key}>
            <Td>{system.name}</Td>
            <Td>{system.description}</Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default SystemsTable;
