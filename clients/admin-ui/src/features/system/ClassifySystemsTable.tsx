import { Stack, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useSelector } from "react-redux";

import ClassificationStatusBadge from "~/features/common/ClassificationStatusBadge";
import { selectClassifyInstanceMap } from "~/features/common/plus.slice";
import { SystemTableCell } from "~/features/common/SystemsCheckboxTable";
import { System } from "~/types/api";

const ClassifySystemsTable = ({ systems }: { systems: System[] }) => {
  const classifyInstanceMap = useSelector(selectClassifyInstanceMap);

  return (
    <Stack>
      <Table size="sm" data-testid="systems-classify-table">
        <Thead>
          <Tr>
            <Th>System Name</Th>
            <Th>Description</Th>
            <Th>Classification Status</Th>
          </Tr>
        </Thead>
        <Tbody>
          {systems.map((system) => {
            const classifyInstance = classifyInstanceMap.get(system.fides_key);
            return (
              <Tr
                key={system.fides_key}
                data-testid={`row-${system.fides_key}`}
              >
                <Td>
                  <SystemTableCell system={system} attribute="name" />
                </Td>
                <Td>
                  <SystemTableCell system={system} attribute="description" />
                </Td>
                <Td data-testid={`status-${system.fides_key}`}>
                  <ClassificationStatusBadge
                    resource="system"
                    status={classifyInstance?.status}
                  />
                </Td>
              </Tr>
            );
          })}
        </Tbody>
      </Table>
    </Stack>
  );
};

export default ClassifySystemsTable;
