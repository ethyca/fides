import {
  Badge,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tooltip,
  Tr,
} from "@fidesui/react";
import { useDispatch, useSelector } from "react-redux";

import { useClassificationsMap } from "~/features/common/plus.slice";
import { Dataset } from "~/types/api";

import { STATUS_DISPLAY } from "./constants";
import {
  selectActiveDatasetFidesKey,
  setActiveDatasetFidesKey,
  useGetAllDatasetsQuery,
} from "./dataset.slice";

const DatasetsTable = () => {
  const dispatch = useDispatch();
  const activeDatasetFidesKey = useSelector(selectActiveDatasetFidesKey);

  const { data: datasets } = useGetAllDatasetsQuery();
  const classificationsMap = useClassificationsMap();

  const handleRowClick = (dataset: Dataset) => {
    // toggle the active dataset
    if (dataset.fides_key === activeDatasetFidesKey) {
      dispatch(setActiveDatasetFidesKey(undefined));
    } else {
      dispatch(setActiveDatasetFidesKey(dataset.fides_key));
    }
  };

  if (!datasets) {
    return <div>Empty state</div>;
  }
  return (
    <Table size="sm" data-testid="dataset-table">
      <Thead>
        <Tr>
          <Th pl={1}>Name</Th>
          <Th pl={1}>Fides Key</Th>
          <Th pl={1}>Description</Th>
          <Th pl={1}>Status</Th>
        </Tr>
      </Thead>
      <Tbody>
        {datasets.map((dataset) => {
          const isActive =
            activeDatasetFidesKey &&
            activeDatasetFidesKey === dataset.fides_key;

          const classification = classificationsMap.get(dataset.fides_key);
          const statusDisplay =
            STATUS_DISPLAY[classification?.status ?? "default"];

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
              <Td pl={1}>{dataset.name}</Td>
              <Td pl={1}>{dataset.fides_key}</Td>
              <Td pl={1}>{dataset.description}</Td>
              <Td pl={1}>
                <Tooltip label={statusDisplay.tooltip}>
                  <Badge
                    variant="solid"
                    colorScheme={statusDisplay.color}
                    data-testid={`dataset-status-${dataset.fides_key}`}
                  >
                    {statusDisplay.title}
                  </Badge>
                </Tooltip>
              </Td>
            </Tr>
          );
        })}
      </Tbody>
    </Table>
  );
};

export default DatasetsTable;
