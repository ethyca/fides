import {
  IconButton,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Text,
} from "@fidesui/react";
import { TrashCanSolidIcon } from "common/Icon/TrashCanSolidIcon";
import React from "react";

import { System } from "~/types/api";

type Props = {
  dataFlowSystems: System[];
  onDataFlowSystemChange: (systems: System[]) => void;
};

export const DataFlowSystemsDeleteTable = ({
  dataFlowSystems,
  onDataFlowSystemChange,
}: Props) => {
  if (dataFlowSystems.length === 0) {
    return null;
  }

  const onDelete = (system: System) => {
    onDataFlowSystemChange(
      dataFlowSystems.filter(
        (dataFlowSystem) => dataFlowSystem.fides_key !== system.fides_key
      )
    );
  };

  return (
    <Table size="sm" data-testid="assign-systems-delete-table">
      <Thead>
        <Tr>
          <Th>System</Th>
          <Th />
        </Tr>
      </Thead>
      <Tbody>
        {dataFlowSystems.map((system) => (
          <Tr
            key={system.fides_key}
            _hover={{ bg: "gray.50" }}
            data-testid={`row-${system.fides_key}`}
          >
            <Td>
              <Text fontSize="xs" lineHeight={4} fontWeight="medium">
                {system.name}
              </Text>
            </Td>
            <Td textAlign="end">
              <IconButton
                background="gray.50"
                aria-label="Unassign data flow from system"
                icon={<TrashCanSolidIcon />}
                variant="outline"
                size="sm"
                onClick={() => onDelete(system)}
                data-testid="unassign-btn"
              />
            </Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};
