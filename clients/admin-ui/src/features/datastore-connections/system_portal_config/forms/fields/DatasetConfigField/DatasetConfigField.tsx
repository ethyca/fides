import {
  Box,
  Button,
  Center,
  HStack,
  Select,
  Spinner,
  Text,
  TextProps,
  VStack,
} from "@fidesui/react";
import { useAlert, useAPIHelper } from "common/hooks";
import {
  useGetDatasetConfigsQuery,
  usePatchDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import React, { ChangeEvent, useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import {
  useGetAllDatasetsQuery,
  useUpsertDatasetsMutation,
} from "~/features/dataset";
import {
  ConnectionConfigurationResponse,
  Dataset,
  DatasetConfigCtlDataset,
} from "~/types/api";

import YamlEditor from "./YamlEditor";

type Props = {
  connectionConfig: ConnectionConfigurationResponse;
};

const DatasetConfigField: React.FC<Props> = ({ connectionConfig }) => {
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const {
    data: connectionConfigDatasets,
    isFetching,
    isLoading,
    isSuccess,
  } = useGetDatasetConfigsQuery(connectionConfig!.key);

  const [patchDatasetConfig] = usePatchDatasetConfigsMutation();
  const [upsertDatasets] = useUpsertDatasetsMutation();
  const {
    data: allDatasets,
    isLoading: isLoadingAllDatasets,
    error: loadAllDatasetsError,
  } = useGetAllDatasetsQuery();

  const [selectedDatasetKey, setSelectedDatasetKey] = useState<
    string | undefined
  >(undefined);
  const [connectionConfigDatasetFidesKey, setConnectionConfigDatasetFidesKey] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (connectionConfigDatasets && connectionConfigDatasets.items.length) {
      setSelectedDatasetKey(
        connectionConfigDatasets.items[0].ctl_dataset.fides_key
      );
      setConnectionConfigDatasetFidesKey(
        connectionConfigDatasets.items[0].ctl_dataset.fides_key
      )
    }
  }, [connectionConfigDatasets]);

  const handlePatchDatasetConfig = async (
    datasetPairs: DatasetConfigCtlDataset[]
  ) => {
    const params: PatchDatasetsConfigRequest = {
      connection_key: connectionConfig?.key as string,
      dataset_pairs: datasetPairs,
    };
    const payload = await patchDatasetConfig(params).unwrap();
    if (payload.failed?.length > 0) {
      errorAlert(payload.failed[0].message);
    } else {
      successAlert("Dataset successfully updated!");
    }
  };

  const handleLinkDataset = async () => {
    if (selectedDatasetKey) {
      try {
        let fidesKey = selectedDatasetKey;
        if (connectionConfigDatasetFidesKey) {
          fidesKey = connectionConfigDatasetFidesKey
        }
        const datasetPairs: DatasetConfigCtlDataset[] = [
          { fides_key: fidesKey, ctl_dataset_fides_key: selectedDatasetKey },
        ];
        handlePatchDatasetConfig(datasetPairs);
      } catch (error) {
        handleError(error);
      }
    }
  };

  const handleSubmitYaml = async (value: unknown) => {
    try {
      setIsSubmitting(true);
      // First update the datasets
      const datasets = Array.isArray(value) ? value : [value];
      const upsertResult = await upsertDatasets(datasets);
      if ("error" in upsertResult) {
        const errorMessage = getErrorMessage(upsertResult.error);
        errorAlert(errorMessage);
        return;
      }

      // Upsert was successful, so we can cast from unknown to Dataset
      const upsertedDatasets = datasets as Dataset[];
      // Then link the updated dataset to the connection config.
      // New entries will have matching keys,
      let pairs: DatasetConfigCtlDataset[] = upsertedDatasets.map((d) => ({
        fides_key: d.fides_key,
        ctl_dataset_fides_key: d.fides_key,
      }));
      // But existing entries might have their dataset keys changed from under them
      if (connectionConfigDatasets && connectionConfigDatasets.items.length) {
        const { items: datasetConfigs } = connectionConfigDatasets;
        pairs = datasetConfigs.map((d, i) => ({
          fides_key: d.fides_key,
          // This will not handle deletions, additions, or even changing order. If we want to support
          // those, we should probably have a different UX
          ctl_dataset_fides_key: upsertedDatasets[i].fides_key,
        }));
      }

      handlePatchDatasetConfig(pairs);
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectDataset = (event: ChangeEvent<HTMLSelectElement>) => {
    setSelectedDatasetKey(event.target.value);
  };

  const datasetSelected =
    selectedDatasetKey !== "" && selectedDatasetKey !== undefined;

  if (
    isFetching ||
    isLoading ||
    (isLoadingAllDatasets && !loadAllDatasetsError)
  ) {
    return (
      <Center>
        <Spinner />
      </Center>
    );
  }

  const datasetsExist = allDatasets && allDatasets.length;

  return (
    <HStack spacing={8} mb={4}>
      {datasetsExist ? (
        <>
          <VStack alignSelf="start" mr={4}>
            <Box data-testid="dataset-selector-section" mb={4}>
              <Select
                size="sm"
                width="fit-content"
                placeholder="Select"
                onChange={handleSelectDataset}
                value={selectedDatasetKey}
                data-testid="dataset-selector"
              >
                {allDatasets.map((ds) => (
                  <option key={ds.fides_key} value={ds.fides_key}>
                    {ds.fides_key}
                  </option>
                ))}
              </Select>
            </Box>
            <Button
              size="sm"
              colorScheme="primary"
              alignSelf="start"
              disabled={!datasetSelected}
              onClick={handleLinkDataset}
              data-testid="save-dataset-link-btn"
            >
              Save
            </Button>
          </VStack>
        </>
      ) : null}
      <Box data-testid="yaml-editor-section">
        {isSuccess && connectionConfigDatasets!?.items ? (
          <YamlEditor
            data={connectionConfigDatasets.items.map(
              (item) => item.ctl_dataset
            )}
            isSubmitting={isSubmitting}
            onSubmit={handleSubmitYaml}
            disabled={datasetSelected}
            // Only render the cancel button if the dataset dropdown view is unavailable
            // onCancel={undefined}
          />
        ) : null}
      </Box>
    </HStack>
  );
};

export default DatasetConfigField;
