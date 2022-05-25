import { Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";

import { Dataset } from "./types";

interface Props {
  datasets: Dataset[] | undefined;
}

const DatasetsTable = ({ datasets }: Props) => {
  if (!datasets) {
    return <div>Empty state</div>;
  }
  return (
    <Table size="sm">
      <Thead>
        <Tr>
          <Th pl={0}>Name</Th>
          <Th pl={0}>Fides Key</Th>
          <Th pl={0}>Description</Th>
        </Tr>
      </Thead>
      <Tbody>
        {datasets.map((dataset) => (
          <Tr key={dataset.fides_key}>
            <Td pl={0}>{dataset.name}</Td>
            <Td pl={0}>{dataset.fides_key}</Td>
            <Td pl={0}>{dataset.description}</Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default DatasetsTable;
