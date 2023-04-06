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

import { DataFlow, System } from "~/types/api";
import { useGetAllSystemsQuery } from "~/features/system";
import { useFormikContext } from "formik";

type Props = {
  dataFlows: DataFlow[];
  onDataFlowSystemChange: (systems: DataFlow[]) => void;
};

export const DataFlowSystemsDeleteTable = ({
  dataFlows,
  onDataFlowSystemChange,
}: Props) => {
  const { setFieldValue } = useFormikContext();
  const { data: systems } = useGetAllSystemsQuery(undefined, {
    // eslint-disable-next-line @typescript-eslint/no-shadow
    selectFromResult: ({ data }) => {
      const dataFlowKeys = dataFlows.map((f) => f.fides_key);
      return {
        data: data
          ? data.filter((s) => dataFlowKeys.indexOf(s.fides_key) > -1)
          : [],
      };
    },
  });

  const onDelete = (dataFlow: System) => {
    const updatedDataFlows = dataFlows.filter(
      (dataFlowSystem) => dataFlowSystem.fides_key !== dataFlow.fides_key
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
        {systems.map((system) => (
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
