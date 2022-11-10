import { Stack, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";

import { SystemTableCell } from "~/features/common/SystemsCheckboxTable";
import { System } from "~/types/api";

const ClassifySystemsTable = ({ systems }: { systems: System[] }) => (
  <Stack>
    <Table size="sm" data-testid="systems-classify-table">
      <Thead>
        <Tr>
          <Th>System Name</Th>
          <Th>Description</Th>
        </Tr>
      </Thead>
      <Tbody>
        {systems.map((system) => (
          <Tr key={system.fides_key}>
            <Td>
              <SystemTableCell system={system} attribute="name" />
            </Td>
            <Td>
              <SystemTableCell system={system} attribute="description" />
            </Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  </Stack>
);

export default ClassifySystemsTable;
