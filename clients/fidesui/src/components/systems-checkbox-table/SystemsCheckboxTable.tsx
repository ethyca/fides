import {
  Box,
  Checkbox,
  Table,
  TableHeadProps,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
} from "fidesui";
import React from "react";

import type { ColumnMetadata } from "../column-dropdown";
import { System } from "../types/api";
import { resolvePath } from "./helpers";

// This component is used within a Chakra Td element. Chakra requires a
// JSX.Element in that context, so all returns in this component need to be wrapped in a fragment.
/* eslint-disable react/jsx-no-useless-fragment */
const SystemTableCell = ({
  system,
  attribute,
}: {
  system: System;
  attribute: string;
}) => {
  if (attribute === "name") {
    return (
      <label htmlFor={`checkbox-${system.fides_key}`}>{system.name}</label>
    );
  }
  if (attribute === "fidesctl_meta.resource_id") {
    return (
      <Box
        whiteSpace="nowrap"
        overflow="hidden"
        textOverflow="ellipsis"
        title={system.fidesctl_meta?.resource_id}
      >
        {system.fidesctl_meta?.resource_id}
      </Box>
    );
  }
  return <>{resolvePath(system, attribute)}</>;
};

interface Props {
  onChange: (systems: System[]) => void;
  allSystems: System[];
  checked: System[];
  columns: ColumnMetadata<System>[];
  tableHeadProps?: TableHeadProps;
}
export const SystemsCheckboxTable = ({
  allSystems,
  checked,
  onChange,
  columns,
  tableHeadProps,
}: Props) => {
  const handleChangeAll = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.checked) {
      onChange(allSystems);
    } else {
      onChange([]);
    }
  };
  const onCheck = (system: System) => {
    const exists = checked.indexOf(system) >= 0;
    if (!exists) {
      onChange([...checked, system]);
    } else {
      onChange(checked.filter((c) => c.fides_key !== system.fides_key));
    }
  };

  const allChecked = allSystems.length === checked.length;

  if (columns.length === 0) {
    return <Text>No columns selected to display</Text>;
  }

  return (
    <Table
      size="sm"
      /* Fixed layout allows individual cells to overflow, without having to give each cell
       * a set width. However, Chakra doesn't expose the tableLayout prop
       * https://github.com/chakra-ui/chakra-ui/issues/6822
       */
      sx={{
        tableLayout: "fixed",
      }}
    >
      <Thead {...tableHeadProps}>
        <Tr>
          <Th width="15px">
            <Checkbox
              title="Select All"
              isChecked={allChecked}
              onChange={handleChangeAll}
            />
          </Th>
          {columns.map((c) => (
            <Th key={c.attribute}>{c.name}</Th>
          ))}
        </Tr>
      </Thead>
      <Tbody>
        {allSystems.map((system) => (
          <Tr key={system.fides_key}>
            <Td>
              <Checkbox
                value={system.fides_key}
                isChecked={checked.indexOf(system) >= 0}
                onChange={() => onCheck(system)}
                data-testid={`checkbox-${system.fides_key}`}
              />
            </Td>
            {columns.map((c) => (
              <Td key={c.attribute}>
                <SystemTableCell system={system} attribute={c.attribute} />
              </Td>
            ))}
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default SystemsCheckboxTable;
