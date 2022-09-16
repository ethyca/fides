import { Box, Select, Spinner } from "@fidesui/react";
import { ChangeEvent, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import { useGetAllDataCategoriesQuery } from "~/features/taxonomy/taxonomy.slice";

import ColumnDropdown from "./ColumnDropdown";
import {
  selectActiveCollectionIndex,
  selectActiveEditor,
  setActiveCollectionIndex,
  setActiveDatasetFidesKey,
  setActiveEditor,
  useGetDatasetByKeyQuery,
} from "./dataset.slice";
import DatasetFieldsTable from "./DatasetFieldsTable";
import EditCollectionDrawer from "./EditCollectionDrawer";
import EditDatasetDrawer from "./EditDatasetDrawer";
import MoreActionsMenu from "./MoreActionsMenu";
import { ColumnMetadata, EditableType } from "./types";

const ALL_COLUMNS: ColumnMetadata[] = [
  { name: "Field Name", attribute: "name" },
  { name: "Description", attribute: "description" },
  { name: "Personal Data Categories", attribute: "data_categories" },
  { name: "Identifiability", attribute: "data_qualifier" },
];

const useDataset = (key: string) => {
  const { data, isLoading } = useGetDatasetByKeyQuery(key);

  return {
    isLoading,
    dataset: data,
  };
};

interface Props {
  fidesKey: string;
}

const DatasetCollectionView = ({ fidesKey }: Props) => {
  const dispatch = useDispatch();
  const { dataset, isLoading } = useDataset(fidesKey);
  const activeCollectionIndex = useSelector(selectActiveCollectionIndex);
  const activeEditor = useSelector(selectActiveEditor);

  const [columns, setColumns] = useState<ColumnMetadata[]>(ALL_COLUMNS);

  // Query subscriptions:
  useGetAllDataCategoriesQuery();

  useEffect(() => {
    if (dataset) {
      dispatch(setActiveDatasetFidesKey(dataset.fides_key));
      dispatch(setActiveCollectionIndex(0));
    }
  }, [dispatch, dataset]);

  useEffect(
    () => () => {
      dispatch(setActiveDatasetFidesKey(undefined));
    },
    // This hook only runs on component un-mount to clear the active dataset.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    []
  );

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
        <Select
          onChange={handleChangeCollection}
          mr={2}
          width="auto"
          data-testid="collection-select"
        >
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
            onModifyCollection={() =>
              dispatch(setActiveEditor(EditableType.COLLECTION))
            }
            onModifyDataset={() =>
              dispatch(setActiveEditor(EditableType.DATASET))
            }
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
            isOpen={activeEditor === EditableType.COLLECTION}
            onClose={() => dispatch(setActiveEditor(undefined))}
          />
        </>
      ) : null}
      {dataset ? (
        <EditDatasetDrawer
          dataset={dataset}
          isOpen={activeEditor === EditableType.DATASET}
          onClose={() => dispatch(setActiveEditor(undefined))}
        />
      ) : null}
    </Box>
  );
};

export default DatasetCollectionView;
