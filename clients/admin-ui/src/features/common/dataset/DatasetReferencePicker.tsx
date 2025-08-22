import {
  AntFlex as Flex,
  AntSelect as Select,
  AntTreeSelect as TreeSelect,
  Box,
  Text,
} from "fidesui";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks/useAlert";
import {
  useGetAllFilteredDatasetsQuery,
  useGetDatasetByKeyQuery,
  useLazyGetDatasetByKeyQuery,
} from "~/features/dataset/dataset.slice";
import { DatasetCollection } from "~/types/api";

import TreeNodeTitle from "./TreeNodeTitle";
import {
  DATASET_REFERENCE_SEPARATOR,
  DatasetTreeNode,
  parseFieldReference,
  transformFieldsToTreeNodes,
  updateTreeNodeChildren,
} from "./utils";

export interface DatasetReferencePickerProps {
  value?: string;
  onChange?: (value: string | undefined) => void;
  disabled?: boolean;
}

// Empty state component
const EmptyState = () => (
  <Box textAlign="center" py={4} color="gray.500">
    <Text>No datasets available</Text>
    <Text fontSize="sm">Create a dataset to start using this feature</Text>
  </Box>
);

export const DatasetReferencePicker = ({
  value,
  onChange,
  disabled = false,
}: DatasetReferencePickerProps) => {
  const [selectedDataset, setSelectedDataset] = useState<string | undefined>();
  const [selectedFieldReference, setSelectedFieldReference] = useState<
    string | undefined
  >();
  const [treeData, setTreeData] = useState<DatasetTreeNode[]>([]);
  const { errorAlert } = useAlert();

  // Load initial datasets (minimal data)
  const { data: datasets, isLoading: datasetsLoading } =
    useGetAllFilteredDatasetsQuery({
      minimal: true,
    });

  // Load selected dataset (skipped when no dataset selected)
  const { data: selectedDatasetData } = useGetDatasetByKeyQuery(
    selectedDataset!,
    { skip: !selectedDataset },
  );

  const [getDatasetByKey] = useLazyGetDatasetByKeyQuery();

  // Transform selected dataset into tree data for collections
  const collectionTreeData = useMemo(() => {
    if (!selectedDatasetData || !selectedDataset) {
      return [];
    }

    return (
      selectedDatasetData.collections?.map((collection: DatasetCollection) => ({
        key: `${selectedDataset}${DATASET_REFERENCE_SEPARATOR}${collection.name}`,
        title: collection.name,
        value: `${selectedDataset}${DATASET_REFERENCE_SEPARATOR}${collection.name}`,
        isLeaf: false,
        selectable: false, // Collections are not selectable
        children: undefined,
      })) || []
    );
  }, [selectedDatasetData, selectedDataset]);

  // Sync collection data to tree state when dataset changes
  useEffect(() => {
    setTreeData(collectionTreeData);
    if (!selectedDataset) {
      setSelectedFieldReference(undefined);
    }
  }, [collectionTreeData, selectedDataset]);

  // Parse incoming value to set initial state
  useEffect(() => {
    if (value) {
      const { datasetKey, collectionName, fieldPath } =
        parseFieldReference(value);
      if (datasetKey) {
        setSelectedDataset(datasetKey);
        if (collectionName && fieldPath) {
          // Keep the full reference for the field selection
          setSelectedFieldReference(value);
        }
      }
    } else {
      setSelectedDataset(undefined);
      setSelectedFieldReference(undefined);
    }
  }, [value]);

  // Dataset options for Select component
  const datasetOptions = useMemo(() => {
    if (!datasets) {
      return [];
    }

    return datasets.map((dataset) => ({
      value: dataset.fides_key,
      label: dataset.name || dataset.fides_key,
    }));
  }, [datasets]);

  // Async load collection fields
  const loadData = useCallback(
    async (treeNode: any) => {
      if (!selectedDataset) {
        return;
      }

      const nodeKey = treeNode.key as string;
      const [, collectionName] = nodeKey.split(DATASET_REFERENCE_SEPARATOR);

      if (!collectionName) {
        return;
      }

      try {
        const dataset = await getDatasetByKey(selectedDataset).unwrap();

        const collection = dataset.collections?.find(
          (c: DatasetCollection) => c.name === collectionName,
        );

        if (collection && collection.fields) {
          const fieldNodes = transformFieldsToTreeNodes(
            collection.fields,
            selectedDataset,
            collectionName,
            "",
          );
          setTreeData((prev) =>
            updateTreeNodeChildren(prev, nodeKey, fieldNodes),
          );
        }
      } catch (error: any) {
        const errorMessage = getErrorMessage(
          error,
          "Failed to load collection fields",
        );
        errorAlert(errorMessage);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [selectedDataset],
  );

  // Handle dataset selection change
  const handleDatasetChange = useCallback(
    (datasetKey: string | undefined) => {
      setSelectedDataset(datasetKey);
      setSelectedFieldReference(undefined);

      // Clear the overall value since field selection is reset
      if (onChange) {
        onChange(undefined);
      }
    },
    [onChange],
  );

  // Handle field selection change
  const handleFieldChange = useCallback(
    (fieldReference: string | undefined) => {
      setSelectedFieldReference(fieldReference);

      // The fieldReference is already in the correct format (dataset:collection:field)
      // from transformFieldsToTreeNodes, so we can pass it directly
      if (onChange) {
        onChange(fieldReference);
      }
    },
    [onChange],
  );

  // Custom title renderer for tree nodes using treeTitleRender prop
  const treeTitleRender = useCallback((nodeData: any) => {
    return <TreeNodeTitle nodeData={nodeData} />;
  }, []);

  // Show empty state if no datasets available
  if (!datasetsLoading && datasets?.length === 0) {
    return <EmptyState />;
  }

  return (
    <Flex gap={8} data-testid="dataset-reference-picker">
      <Select
        value={selectedDataset}
        onChange={handleDatasetChange}
        options={datasetOptions}
        placeholder="Select a dataset"
        disabled={disabled}
        loading={datasetsLoading}
        allowClear
        showSearch
        style={{ width: "50%" }}
        data-testid="dataset-select"
      />

      <TreeSelect
        value={selectedFieldReference}
        onChange={handleFieldChange}
        treeData={treeData}
        loadData={loadData}
        placeholder="Select a field"
        disabled={disabled || !selectedDataset}
        allowClear
        showSearch
        style={{ width: "50%" }}
        treeNodeFilterProp="title"
        treeTitleRender={treeTitleRender}
        data-testid="field-tree-select"
      />
    </Flex>
  );
};
