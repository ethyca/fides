import { Table, Tbody, Td, Th, Thead, Tr } from "@fidesui/react";
import { useRouter } from "next/router";
import { useDispatch, useSelector } from "react-redux";

import { usePollForClassifications } from "~/features/common/classifications";
import { useFeatures } from "~/features/common/features";
import ClassificationStatusBadge from "~/features/plus/ClassificationStatusBadge";
import { selectDatasetClassifyInstanceMap } from "~/features/plus/plus.slice";
import { Dataset, GenerateTypes } from "~/types/api";

import {
  setActiveDatasetFidesKey,
  useGetAllDatasetsQuery,
} from "./dataset.slice";

const DatasetsTable = () => {
  const dispatch = useDispatch();
  const router = useRouter();
  const { data: datasets } = useGetAllDatasetsQuery();
  const features = useFeatures();
  usePollForClassifications({
    resourceType: GenerateTypes.DATASETS,
    skip: !features.plus,
  });
  const classifyInstanceMap = useSelector(selectDatasetClassifyInstanceMap);

  const handleRowClick = (dataset: Dataset) => {
    dispatch(setActiveDatasetFidesKey(dataset.fides_key));
    router.push(`/dataset/${dataset.fides_key}`);
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
          {features.plus ? (
            <Th data-testid="dataset-table__status-table-header" pl={1}>
              Status
            </Th>
          ) : null}
        </Tr>
      </Thead>
      <Tbody>
        {datasets.map((dataset) => {
          const classifyDataset = classifyInstanceMap.get(dataset.fides_key);

          return (
            <Tr
              key={dataset.fides_key}
              _hover={{ bg: "gray.50" }}
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

              <Td pl={1} data-testid={`dataset-status-${dataset.fides_key}`}>
                {features.plus && classifyDataset?.status ? (
                  <ClassificationStatusBadge
                    resource={GenerateTypes.DATASETS}
                    status={classifyDataset?.status}
                  />
                ) : null}
              </Td>
            </Tr>
          );
        })}
      </Tbody>
    </Table>
  );
};

export default DatasetsTable;
