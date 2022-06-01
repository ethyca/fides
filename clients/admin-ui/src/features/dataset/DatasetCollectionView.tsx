import { Box, Select, Spinner } from "@fidesui/react";
import { ChangeEvent, useEffect, useState } from "react";

import { FidesKey } from "../common/fides-types";
import ColumnDropdown from "./ColumnDropdown";
import { useGetDatasetByKeyQuery } from "./dataset.slice";
import DatasetFieldsTable from "./DatasetFieldsTable";
import { ColumnMetadata, DatasetCollection } from "./types";

const ALL_COLUMNS: ColumnMetadata[] = [
  { name: "Field Name", attribute: "name" },
  { name: "Description", attribute: "description" },
  { name: "Personal Data Categories", attribute: "data_categories" },
  { name: "Identifiability", attribute: "data_qualifier" },
];

const useDataset = (key: FidesKey) => {
  const { data, isLoading } = useGetDatasetByKeyQuery(key);

  return {
    isLoading,
    dataset: data,
  };
};

interface Props {
  fidesKey: FidesKey;
}

const DatasetCollectionView = ({ fidesKey }: Props) => {
  const { dataset, isLoading } = useDataset(fidesKey);
  const [activeCollection, setActiveCollection] = useState<
    DatasetCollection | undefined
  >();
  const [columns, setColumns] = useState<ColumnMetadata[]>(ALL_COLUMNS);

  useEffect(() => {
    if (dataset) {
      setActiveCollection(dataset.collections[0]);
    } else {
      setActiveCollection(undefined);
    }
  }, [dataset]);

  if (!dataset) {
    return <div>Dataset not found</div>;
  }

  const { collections } = dataset;

  const handleChangeCollection = (event: ChangeEvent<HTMLSelectElement>) => {
    const collection = collections.filter(
      (c) => c.name === event.target.value
    )[0];
    setActiveCollection(collection);
  };

  if (isLoading) {
    return <Spinner />;
  }

  return (
    <Box>
      <Box mb={4} display="flex" justifyContent="space-between">
        <Select onChange={handleChangeCollection} mr={2} width="auto">
          {collections.map((collection) => (
            <option key={collection.name} value={collection.name}>
              {collection.name}
            </option>
          ))}
        </Select>
        <ColumnDropdown
          allColumns={ALL_COLUMNS}
          selectedColumns={columns}
          onChange={setColumns}
        />
      </Box>
      {activeCollection && (
        <DatasetFieldsTable
          fields={activeCollection.fields}
          columns={columns}
        />
      )}
    </Box>
  );
};

export default DatasetCollectionView;
