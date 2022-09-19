import { Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useDispatch, useSelector } from "react-redux";

import { Dataset } from "~/types/api";

import { selectActiveDataset, setActiveDataset } from "./dataset.slice";

interface Props {
  datasets: Dataset[] | undefined;
}

const DatasetsTable = ({ datasets }: Props) => {
  const dispatch = useDispatch();
  const activeDataset = useSelector(selectActiveDataset);

  const handleRowClick = (dataset: Dataset) => {
    // toggle the active dataset
    if (dataset.fides_key === activeDataset?.fides_key) {
      dispatch(setActiveDataset(null));
    } else {
      dispatch(setActiveDataset(dataset));
    }
  };

  if (!datasets) {
    return <div>Empty state</div>;
  }
  return (
    <Table size="sm" data-testid="dataset-table">
      <Thead>
        <Tr>
          <Th pl={0}>Name</Th>
          <Th pl={0}>Fides Key</Th>
          <Th pl={0}>Description</Th>
        </Tr>
      </Thead>
      <Tbody>
        {datasets.map((dataset) => {
          const isActive =
            activeDataset && activeDataset.fides_key === dataset.fides_key;

          return (
            <Tr
              key={dataset.fides_key}
              _hover={{ bg: isActive ? undefined : "gray.50" }}
              backgroundColor={isActive ? "complimentary.50" : undefined}
              tabIndex={0}
              onClick={() => handleRowClick(dataset)}
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  handleRowClick(dataset);
                }
              }}
              cursor="pointer"
              data-testid={`dataset-row-${dataset.fides_key}`}
            >
              <Td pl={0}>{dataset.name}</Td>
              <Td pl={0}>{dataset.fides_key}</Td>
              <Td pl={0}>{dataset.description}</Td>
            </Tr>
          );
        })}
      </Tbody>
    </Table>
  );
};

export default DatasetsTable;
