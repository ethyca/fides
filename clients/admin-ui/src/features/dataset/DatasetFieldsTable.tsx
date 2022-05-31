import { Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";

import { DatasetField } from "./types";

interface Props {
  fields: DatasetField[];
}

const DatasetFieldsTable = ({ fields }: Props) => (
  <Table size="sm">
    <Thead>
      <Tr>
        <Th pl={0}>Field Name</Th>
        <Th pl={0}>Description</Th>
        <Th pl={0}>Identifiability</Th>
      </Tr>
    </Thead>
    <Tbody>
      {fields.map((field) => (
        <Tr key={field.name}>
          <Td pl={0}>{field.name}</Td>
          <Td pl={0}>{field.description}</Td>
          <Td pl={0}>{field.data_qualifier}</Td>
        </Tr>
      ))}
    </Tbody>
  </Table>
);

export default DatasetFieldsTable;
