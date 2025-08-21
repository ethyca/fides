import { AntTreeSelect as TreeSelect, Box, Text } from "fidesui";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useAlert } from "~/features/common/hooks/useAlert";
import {
  useGetAllFilteredDatasetsQuery,
  useLazyGetDatasetByKeyQuery,
} from "~/features/dataset/dataset.slice";
import { Dataset, DatasetCollection } from "~/types/api";

import TreeNodeTitle from "./TreeNodeTitle";
import {
  DATASET_REFERENCE_SEPARATOR,
  DatasetTreeNode,
  transformFieldsToTreeNodes,
  updateTreeNodeChildren,
} from "./utils";

export interface DatasetReferencePickerProps {
  value?: string;
  onChange?: (value: string | undefined) => void;
  placeholder?: string;
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
  placeholder = "Select a dataset field",
  disabled = false,
}: DatasetReferencePickerProps) => {
  const [treeData, setTreeData] = useState<DatasetTreeNode[]>([]);
  const [datasetCache, setDatasetCache] = useState<Map<string, Dataset>>(
    new Map(),
  );
  const { errorAlert } = useAlert();

  // Load initial datasets (minimal data)
  const { data: datasets, isLoading } = useGetAllFilteredDatasetsQuery({
    minimal: true,
  });
  const [getDatasetByKey] = useLazyGetDatasetByKeyQuery();

  // Memoized tree data transformation
  const initialTreeData = useMemo(() => {
    if (!datasets) {
      return [];
    }

    return datasets.map((dataset) => {
      const title = dataset.name || dataset.fides_key;
      return {
        key: dataset.fides_key,
        title,
        value: dataset.fides_key,
        isLeaf: false,
        selectable: false, // Datasets are not selectable
        children: undefined,
      };
    });
  }, [datasets]);

  // Initialize tree with datasets
  useEffect(() => {
    setTreeData(initialTreeData);
  }, [initialTreeData]);

  // Async load collections and fields with caching and error handling
  const loadData = useCallback(
    async (treeNode: any) => {
      const nodeKey = treeNode.key as string;

      try {
        if (!nodeKey.includes(DATASET_REFERENCE_SEPARATOR)) {
          // Load dataset collections - check cache first
          let dataset = datasetCache.get(nodeKey);
          if (!dataset) {
            const fetchedDataset = await getDatasetByKey(nodeKey).unwrap();
            dataset = fetchedDataset;
            setDatasetCache((prev) =>
              new Map(prev).set(nodeKey, fetchedDataset),
            );
          }

          const collectionNodes: DatasetTreeNode[] =
            dataset.collections?.map((collection: DatasetCollection) => ({
              key: `${nodeKey}${DATASET_REFERENCE_SEPARATOR}${collection.name}`,
              title: collection.name,
              value: `${nodeKey}${DATASET_REFERENCE_SEPARATOR}${collection.name}`,
              isLeaf: false,
              selectable: false, // Collections are not selectable
              children: undefined,
            })) || [];

          setTreeData((prev) =>
            updateTreeNodeChildren(prev, nodeKey, collectionNodes),
          );
        } else {
          // Load collection fields
          const [datasetKey, collectionName] = nodeKey.split(
            DATASET_REFERENCE_SEPARATOR,
          );

          // Check cache first
          let dataset = datasetCache.get(datasetKey);
          if (!dataset) {
            const fetchedDataset = await getDatasetByKey(datasetKey).unwrap();
            dataset = fetchedDataset;
            setDatasetCache((prev) =>
              new Map(prev).set(datasetKey, fetchedDataset),
            );
          }

          const collection = dataset.collections?.find(
            (c: DatasetCollection) => c.name === collectionName,
          );

          if (collection && collection.fields) {
            const fieldNodes = transformFieldsToTreeNodes(
              collection.fields,
              datasetKey,
              collectionName,
              "",
            );
            setTreeData((prev) =>
              updateTreeNodeChildren(prev, nodeKey, fieldNodes),
            );
          }
        }
      } catch (error: any) {
        const errorMessage = getErrorMessage(
          error,
          "Failed to load dataset data",
        );
        errorAlert(errorMessage);
      }
    },
    [getDatasetByKey, datasetCache, errorAlert],
  );

  const handleChange = useCallback(
    (newValue: string | undefined) => {
      if (onChange) {
        onChange(newValue);
      }
    },
    [onChange],
  );

  // Custom title renderer for tree nodes using treeTitleRender prop
  const treeTitleRender = useCallback((nodeData: any) => {
    return <TreeNodeTitle nodeData={nodeData} />;
  }, []);

  // Show empty state if no datasets available
  if (!isLoading && datasets?.length === 0) {
    return <EmptyState />;
  }

  return (
    <TreeSelect
      value={value}
      onChange={handleChange}
      treeData={treeData}
      loadData={loadData}
      placeholder={placeholder}
      disabled={disabled}
      loading={isLoading}
      allowClear
      showSearch
      style={{ width: "100%" }}
      treeNodeFilterProp="title"
      treeTitleRender={treeTitleRender}
      data-testid="dataset-reference-picker"
    />
  );
};
