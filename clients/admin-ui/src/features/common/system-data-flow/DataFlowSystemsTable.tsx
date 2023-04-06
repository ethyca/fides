import {
  Box,
  Switch,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
  Text,
} from "@fidesui/react";
import React from "react";

import { System } from "~/types/api";

type Props = {
  allSystems: System[];
  dataFlowSystems: System[];
  onChange: (systems: System[]) => void;
};

const DataFlowSystemsTable = ({
  allSystems,
  dataFlowSystems,
  onChange,
}: Props) => {
  const handleToggle = (system: System) => {
    const isAssigned = !!dataFlowSystems.find(
      (assigned) => assigned.fides_key === system.fides_key
    );
    if (isAssigned) {
      onChange(
        dataFlowSystems.filter(
          (assignedSystem) => assignedSystem.fides_key !== system.fides_key
        )
      );
    } else {
      onChange([...dataFlowSystems, system]);
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
            <Th textAlign="right">Set as Source</Th>
          </Tr>
        </Thead>
        <Tbody>
          {allSystems.map((system) => {
            const isAssigned = !!dataFlowSystems.find(
              (assigned) => assigned.fides_key === system.fides_key
            );
            return (
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
                <Td textAlign="right">
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

export default DataFlowSystemsTable;
