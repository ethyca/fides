import { Box, Button, Select } from "@fidesui/react";
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
  const { dataset } = useDataset(fidesKey);
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

  return (
    <Box>
      <Box mb={4} display="flex" width="auto">
        <Select onChange={handleChangeCollection} mr={2}>
          {collections.map((collection) => (
            <option key={collection.name} value={collection.name}>
              {collection.name}
            </option>
          ))}
        </Select>
        <Button>Modify collection</Button>
      </Box>
      {activeCollection && (
        <DatasetFieldsTable fields={activeCollection.fields} />
      )}
    </Box>
  );
};

export default DatasetCollectionView;
