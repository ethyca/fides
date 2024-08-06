import { Box, HStack, Select, Spinner } from "fidesui";
import { ChangeEvent, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import {
  ColumnDropdown,
  ColumnMetadata,
} from "~/features/common/ColumnDropdown";
import { useFeatures } from "~/features/common/features";
import { useGetClassifyDatasetQuery } from "~/features/plus/plus.slice";
import { useGetAllDataCategoriesQuery } from "~/features/taxonomy/taxonomy.slice";
import { DatasetField } from "~/types/api";

import ApproveClassification from "./ApproveClassification";
import {
  selectActiveCollection,
  selectActiveCollections,
  selectActiveEditor,
  setActiveCollectionIndex,
  setActiveDatasetFidesKey,
  setActiveEditor,
  useGetDatasetByKeyQuery,
} from "./dataset.slice";
import DatasetFieldsTable from "./DatasetFieldsTable";
import DatasetHeading from "./DatasetHeading";
import EditCollectionDrawer from "./EditCollectionDrawer";
import EditDatasetDrawer from "./EditDatasetDrawer";
import MoreActionsMenu from "./MoreActionsMenu";
import { EditableType } from "./types";

const ALL_COLUMNS: ColumnMetadata<DatasetField>[] = [
  { name: "Field Name", attribute: "name" },
  { name: "Description", attribute: "description" },
  { name: "Personal Data Categories", attribute: "data_categories" },
];

/**
 * Query subscriptions shared between vies within this feature.
 */
const useSubscriptions = (key: string) => {
  const { data: dataset, isLoading: isDatasetLoading } =
    useGetDatasetByKeyQuery(key);
  const features = useFeatures();
  const { isLoading: isClassifyDatasetLoading } = useGetClassifyDatasetQuery(
    key,
    {
      skip: !features.plus,
    },
  );
  useGetAllDataCategoriesQuery();

  return {
    isLoading: isDatasetLoading || isClassifyDatasetLoading,
    dataset,
  };
};

interface Props {
  fidesKey: string;
}

const DatasetCollectionView = ({ fidesKey }: Props) => {
  const dispatch = useDispatch();
  const { dataset, isLoading } = useSubscriptions(fidesKey);
  const activeCollections = useSelector(selectActiveCollections);
  const activeCollection = useSelector(selectActiveCollection);
  const activeEditor = useSelector(selectActiveEditor);

  const [columns, setColumns] =
    useState<ColumnMetadata<DatasetField>[]>(ALL_COLUMNS);

  // Query subscriptions:
  useGetAllDataCategoriesQuery();

  useEffect(() => {
    if (dataset) {
      dispatch(setActiveDatasetFidesKey(dataset.fides_key));
    }
  }, [dispatch, dataset]);

  useEffect(
    () => () => {
      dispatch(setActiveDatasetFidesKey(undefined));
    },
    // This hook only runs on component un-mount to clear the active dataset.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const handleChangeCollection = (event: ChangeEvent<HTMLSelectElement>) => {
    dispatch(setActiveCollectionIndex(event.target.selectedIndex));
  };

  if (isLoading) {
    return <Spinner />;
  }

  if (!dataset) {
    return <div>Dataset not found</div>;
  }

  return (
    <Box>
      <DatasetHeading />

      <HStack mb={4}>
        <Select
          onChange={handleChangeCollection}
          width="fit-content"
          flexShrink={0}
          data-testid="collection-select"
        >
          {(activeCollections ?? []).map((collection) => (
            <option key={collection.name} value={collection.name}>
              {collection.name}
            </option>
          ))}
        </Select>
        <ApproveClassification />
        <Box>
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
      </HStack>

      <DatasetFieldsTable columns={columns} />

      {activeCollection ? (
        <EditCollectionDrawer
          collection={activeCollection}
          isOpen={activeEditor === EditableType.COLLECTION}
          onClose={() => dispatch(setActiveEditor(undefined))}
        />
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
