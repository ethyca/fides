import { Stack, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useState } from "react";
import { useSelector } from "react-redux";

import { SystemTableCell } from "~/features/common/SystemsCheckboxTable";
import ClassificationStatusBadge from "~/features/plus/ClassificationStatusBadge";
import { selectSystemClassifyInstanceMap } from "~/features/plus/plus.slice";
import { GenerateTypes, System } from "~/types/api";

import EditClassifySystemDrawer from "./EditClassifySystemDrawer";

const ClassifySystemsTable = ({ systems }: { systems: System[] }) => {
  const classifyInstanceMap = useSelector(selectSystemClassifyInstanceMap);
  const [activeSystem, setActiveSystem] = useState<System | undefined>(
    undefined
  );

  const handleClick = (system: System) => {
    setActiveSystem(system);
  };

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
                _hover={{ bg: "gray.50" }}
                cursor="pointer"
                onClick={() => handleClick(system)}
              >
                <Td>
                  <SystemTableCell system={system} attribute="name" />
                </Td>
                <Td>
                  <SystemTableCell system={system} attribute="description" />
                </Td>
                <Td data-testid={`status-${system.fides_key}`}>
                  <ClassificationStatusBadge
                    resource={GenerateTypes.SYSTEMS}
                    status={classifyInstance?.status}
                  />
                </Td>
              </Tr>
            );
          })}
        </Tbody>
      </Table>
      {activeSystem ? (
        <EditClassifySystemDrawer
          system={activeSystem}
          isOpen={activeSystem != null}
          onClose={() => setActiveSystem(undefined)}
        />
      ) : null}
    </Stack>
  );
};

export default ClassifySystemsTable;
