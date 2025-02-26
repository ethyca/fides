import {
  AntSwitch as Switch,
  Box,
  Table,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "fidesui";
import { useFormikContext } from "formik";
import React from "react";

import { DataFlow, System } from "~/types/api";

type Props = {
  allSystems: System[];
  dataFlowSystems: DataFlow[];
  onChange: (dataFlows: DataFlow[]) => void;
  flowType: string;
};

const DataFlowSystemsTable = ({
  allSystems,
  dataFlowSystems,
  onChange,
  flowType,
}: Props) => {
  const { setFieldValue } = useFormikContext();
  const handleToggle = (system: System) => {
    const isAssigned = !!dataFlowSystems.find(
      (assigned) => assigned.fides_key === system.fides_key,
    );
    if (isAssigned) {
      const updatedDataFlows = dataFlowSystems.filter(
        (assignedSystem) => assignedSystem.fides_key !== system.fides_key,
      );
      setFieldValue("dataFlowSystems", updatedDataFlows);
      onChange(updatedDataFlows);
    } else {
      const updatedDataFlows = [
        ...dataFlowSystems,
        { fides_key: system.fides_key, type: "system" },
      ];

      setFieldValue("dataFlowSystems", updatedDataFlows);
      onChange(updatedDataFlows);
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
            <Th textAlign="right">Set as {flowType}</Th>
          </Tr>
        </Thead>
        <Tbody>
          {allSystems.map((system) => {
            const isAssigned = !!dataFlowSystems.find(
              (assigned) => assigned.fides_key === system.fides_key,
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
                    checked={isAssigned}
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
