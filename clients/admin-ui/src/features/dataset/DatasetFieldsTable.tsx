import { Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useState } from "react";

import { DatasetField } from "./types";

interface ColumnMetadata {
  name: string;
  attribute: keyof DatasetField;
}
const ALL_COLUMNS: ColumnMetadata[] = [
  { name: "Field Name", attribute: "name" },
  { name: "Description", attribute: "description" },
  { name: "Personal Data Categories", attribute: "data_categories" },
  { name: "Identifiability", attribute: "data_qualifier" },
];
interface Props {
  fields: DatasetField[];
}

const DatasetFieldsTable = ({ fields }: Props) => {
  const [columns, setColumns] = useState<ColumnMetadata[]>(ALL_COLUMNS);
  return (
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
};

export default DatasetFieldsTable;
