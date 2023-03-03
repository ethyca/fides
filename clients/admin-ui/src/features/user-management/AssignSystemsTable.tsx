import { Switch, Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";

import { System } from "~/types/api";

const AssignSystemsTable = ({
  allSystems,
  assignedSystems,
  onChange,
}: {
  allSystems: System[];
  assignedSystems: System[];
  onChange: (systems: System[]) => void;
}) => {
  const handleToggle = (system: System) => {
    if (assignedSystems.includes(system)) {
      onChange(
        assignedSystems.filter(
          (assignedSystem) => assignedSystem.fides_key !== system.fides_key
        )
      );
    } else {
      onChange([...assignedSystems, system]);
    }
  };

  return (
    <Table size="sm" data-testid="user-management-table">
      <Thead>
        <Tr>
          <Th>System</Th>
          <Th>Assign</Th>
        </Tr>
      </Thead>
      <Tbody>
        {allSystems.map((system) => {
          const isAssigned = assignedSystems.includes(system);
          return (
            <Tr
              key={system.fides_key}
              _hover={{ bg: "gray.50" }}
              data-testid={`row-${system.fides_key}`}
            >
              <Td>{system.name}</Td>
              <Td>
                <Switch
                  isChecked={isAssigned}
                  onChange={() => handleToggle(system)}
                />
              </Td>
            </Tr>
          );
        })}
      </Tbody>
    </Table>
  );
};

export default AssignSystemsTable;
