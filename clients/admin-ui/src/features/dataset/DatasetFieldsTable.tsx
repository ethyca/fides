import { Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";

import { ColumnMetadata, DatasetField } from "./types";

interface Props {
  fields: DatasetField[];
  columns: ColumnMetadata[];
}

const DatasetFieldsTable = ({ fields, columns }: Props) => (
  <Table size="sm">
    <Thead>
      <Tr>
        {columns.map((c) => (
          <Th key={c.name} pl={0}>
            {c.name}
          </Th>
        ))}
      </Tr>
    </Thead>
    <Tbody>
      {fields.map((field) => (
        <Tr key={field.name}>
          {columns.map((c) => (
            <Td key={`${field.name}-${field[c.attribute]}`} pl={0}>
              {field[c.attribute]}
            </Td>
          ))}
        </Tr>
      ))}
    </Tbody>
  </Table>
);

export default DatasetFieldsTable;
