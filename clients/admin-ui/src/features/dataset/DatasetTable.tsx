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
        </Tr>
      </Thead>
      <Tbody>
        <Tr>
          <Td>hi</Td>
        </Tr>
      </Tbody>
    </Table>
  );
};

export default DatasetsTable;
