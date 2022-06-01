import { Box, Select, Spinner } from "@fidesui/react";
import { ChangeEvent, useEffect, useState } from "react";

import { FidesKey } from "../common/fides-types";
import { useGetDatasetByKeyQuery } from "./dataset.slice";
import DatasetFieldsTable from "./DatasetFieldsTable";
import { DatasetCollection } from "./types";

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
      <Box mb={4} display="flex">
        <Select onChange={handleChangeCollection} mr={2} width="auto">
          {collections.map((collection) => (
            <option key={collection.name} value={collection.name}>
              {collection.name}
            </option>
          ))}
        </Select>
      </Box>
      {activeCollection && (
        <DatasetFieldsTable fields={activeCollection.fields} />
      )}
    </Box>
  );
};

export default DatasetCollectionView;
