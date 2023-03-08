import {
  Box,
  IconButton,
  Switch,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  TrashCanSolidIcon,
} from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import { System } from "~/types/api";

import {
  selectActiveUserId,
  selectActiveUsersManagedSystems,
  useGetUserManagedSystemsQuery,
  useRemoveUserManagedSystemMutation,
} from "./user-management.slice";

export const AssignSystemsDeleteTable = () => {
  const activeUserId = useAppSelector(selectActiveUserId);
  useGetUserManagedSystemsQuery(activeUserId as string, {
    skip: !activeUserId,
  });
  const assignedSystems = useAppSelector(selectActiveUsersManagedSystems);

  const [removeUserManagedSystemTrigger] = useRemoveUserManagedSystemMutation();
  const handleDelete = async (system: System) => {
    // TODO: the designs don't have this, but we probably want a confirmation modal
    if (!activeUserId) {
      return;
    }
    // TODO: error handling
    const result = await removeUserManagedSystemTrigger({
      userId: activeUserId,
      systemKey: system.fides_key,
    });
    console.log({ result });
  };

  if (assignedSystems.length === 0) {
    return null;
  }

  return (
    <Table size="sm" data-testid="assign-systems-delete-table">
      <Thead>
        <Tr>
          <Th>System</Th>
          <Th />
        </Tr>
      </Thead>
      <Tbody>
        {assignedSystems.map((system) => (
          <Tr
            key={system.fides_key}
            _hover={{ bg: "gray.50" }}
            data-testid={`row-${system.fides_key}`}
          >
            <Td>{system.name}</Td>
            <Td>
              <IconButton
                aria-label="Unassign system from user"
                icon={<TrashCanSolidIcon />}
                size="xs"
                onClick={() => handleDelete(system)}
                data-testid="unassign-btn"
              />
            </Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

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
    const isAssigned = !!assignedSystems.find(
      (assigned) => assigned.fides_key === system.fides_key
    );
    if (isAssigned) {
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
    <Box overflowY="auto" maxHeight="300px">
      <Table size="sm" data-testid="assign-systems-table" maxHeight="50vh" overflowY="scroll">
        <Thead position="sticky" top={0} background="white" zIndex={1}>
          <Tr>
            <Th>System</Th>
            <Th>Assign</Th>
          </Tr>
        </Thead>
        <Tbody>
          {allSystems.map((system) => {
            const isAssigned = !!assignedSystems.find(
                (assigned) => assigned.fides_key === system.fides_key
            );
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
                        data-testid="assign-switch"
                    />
                  </Td>
                </Tr>
            );
          })}
        </Tbody>
      </Table>
    </Box>
  );
};

export default AssignSystemsTable;
