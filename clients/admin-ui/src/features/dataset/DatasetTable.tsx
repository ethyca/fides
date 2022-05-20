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
          <Th>Name</Th>
          <Th>Description</Th>
        </Tr>
      </Thead>
      <Tbody>
        {datasets.map((dataset) => (
          <Tr key={dataset.fides_key}>
            <Td>{dataset.name}</Td>
            <Td>{dataset.description}</Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  );
};

export default DatasetsTable;
