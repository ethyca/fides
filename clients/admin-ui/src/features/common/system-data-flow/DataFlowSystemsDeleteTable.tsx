import { TrashCanSolidIcon } from "common/Icon/TrashCanSolidIcon";
import { AntButton, Table, Tbody, Td, Text, Th, Thead, Tr } from "fidesui";
import { useFormikContext } from "formik";
import React from "react";

import { DataFlow, System } from "~/types/api";

type Props = {
  systems: System[];
  dataFlows: DataFlow[];
  onDataFlowSystemChange: (systems: DataFlow[]) => void;
};

export const DataFlowSystemsDeleteTable = ({
  systems,
  dataFlows,
  onDataFlowSystemChange,
}: Props) => {
  const { setFieldValue } = useFormikContext();

  const dataFlowKeys = dataFlows.map((f) => f.fides_key);

  const onDelete = (dataFlow: System) => {
    const updatedDataFlows = dataFlows.filter(
      (dataFlowSystem) => dataFlowSystem.fides_key !== dataFlow.fides_key,
    );
    setFieldValue("dataFlowSystems", updatedDataFlows);
    onDataFlowSystemChange(updatedDataFlows);
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
        {systems
          .filter((system) => dataFlowKeys.includes(system.fides_key))
          .map((system) => (
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
                <AntButton
                  aria-label="Unassign data flow from system"
                  icon={<TrashCanSolidIcon />}
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
