import {
  Box,
  IconButton,
  Switch,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  TrashCanSolidIcon,
  useDisclosure,
  useToast,
} from "@fidesui/react";
import ConfirmationModal from "common/ConfirmationModal";
import { getErrorMessage } from "common/helpers";
import { errorToastParams, successToastParams } from "common/toast";
import React from "react";

import { useAppSelector } from "~/app/hooks";
import { System } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import {
  selectActiveUserId,
  selectActiveUsersManagedSystems,
  useGetUserManagedSystemsQuery,
  useRemoveUserManagedSystemMutation,
} from "./user-management.slice";

export const AssignSystemsDeleteTable = () => {
  const activeUserId = useAppSelector(selectActiveUserId);
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  useGetUserManagedSystemsQuery(activeUserId as string, {
    skip: !activeUserId,
  });
  const assignedSystems = useAppSelector(selectActiveUsersManagedSystems);
  const toast = useToast();
  const [removeUserManagedSystemTrigger] = useRemoveUserManagedSystemMutation();
  const handleDelete = async (system: System) => {
    if (!activeUserId) {
      return;
    }
    const result = await removeUserManagedSystemTrigger({
      userId: activeUserId,
      systemKey: system.fides_key,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Successfully removed system"));
      onDeleteClose();
    }
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
                onClick={onDeleteOpen}
                data-testid="unassign-btn"
              />
              <ConfirmationModal
                isOpen={deleteIsOpen}
                onClose={onDeleteClose}
                onConfirm={() => handleDelete(system)}
                title="Delete System"
                continueButtonText="Yes, Remove System"
                message={
                  <Text>Are you sure you want to remove this system?</Text>
                }
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
      <Table
        size="sm"
        data-testid="assign-systems-table"
        maxHeight="50vh"
        overflowY="scroll"
      >
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
