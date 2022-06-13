import { Box, Select, Spinner, useToast } from "@fidesui/react";
import { useRouter } from "next/router";
import { ChangeEvent, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { FidesKey } from "../common/fides-types";
import { successToastParams } from "../common/toast";
import ColumnDropdown from "./ColumnDropdown";
import {
  selectActiveCollectionIndex,
  setActiveCollectionIndex,
  setActiveDataset,
  useGetDatasetByKeyQuery,
} from "./dataset.slice";
import DatasetFieldsTable from "./DatasetFieldsTable";
import EditCollectionDrawer from "./EditCollectionDrawer";
import MoreActionsMenu from "./MoreActionsMenu";
import { ColumnMetadata } from "./types";

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
  const dispatch = useDispatch();
  const { dataset, isLoading } = useDataset(fidesKey);
  const activeCollectionIndex = useSelector(selectActiveCollectionIndex);
  const [columns, setColumns] = useState<ColumnMetadata[]>(ALL_COLUMNS);
  const [isModifyingCollection, setIsModifyingCollection] = useState(false);

  const router = useRouter();
  const toast = useToast();
  const { fromLoad } = router.query;

  if (dataset) {
    dispatch(setActiveDataset(dataset));
  }

  useEffect(() => {
    if (dataset) {
      dispatch(setActiveDataset(dataset));
    }
  }, [dispatch, dataset]);

  useEffect(() => {
    dispatch(setActiveCollectionIndex(0));
  }, [dispatch]);

  useEffect(() => {
    if (fromLoad) {
      toast(successToastParams("Successfully loaded dataset"));
    }
  }, [fromLoad, toast]);

  if (isLoading) {
    return <Spinner />;
  }

  if (!dataset) {
    return <div>Dataset not found</div>;
  }

  const { collections } = dataset;
  const activeCollection =
    activeCollectionIndex != null ? collections[activeCollectionIndex] : null;

  const handleChangeCollection = (event: ChangeEvent<HTMLSelectElement>) => {
    dispatch(setActiveCollectionIndex(event.target.selectedIndex));
  };

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
        <Box display="flex">
          <Box mr={2}>
            <ColumnDropdown
              allColumns={ALL_COLUMNS}
              selectedColumns={columns}
              onChange={setColumns}
            />
          </Box>
          <MoreActionsMenu
            onModifyCollection={() => {
              setIsModifyingCollection(true);
            }}
          />
        </Box>
      </Box>
      {activeCollection ? (
        <>
          <DatasetFieldsTable
            fields={activeCollection.fields}
            columns={columns}
          />
          <EditCollectionDrawer
            collection={activeCollection}
            isOpen={isModifyingCollection}
            onClose={() => setIsModifyingCollection(false)}
          />
        </>
      ) : null}
    </Box>
  );
};

export default DatasetCollectionView;
