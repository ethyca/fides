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
import { selectConnectionTypeState } from "connection-type/connection-type.slice";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  usePatchDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import { useRouter } from "next/router";
import React, { ChangeEvent, useEffect, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import { DATASTORE_CONNECTION_ROUTE } from "~/features/common/nav/v2/routes";
import {
  useGetAllDatasetsQuery,
  useUpsertDatasetsMutation,
} from "~/features/dataset";
import { Dataset, DatasetConfigCtlDataset } from "~/types/api";

import YamlEditorForm from "./forms/YamlEditorForm";

const Copy = ({ children, ...props }: TextProps) => (
  <Text color="gray.700" fontSize="14px" {...props}>
    {children}
  </Text>
);

const DatasetConfiguration: React.FC = () => {
  const router = useRouter();
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { connection } = useAppSelector(selectConnectionTypeState);
  const { data, isFetching, isLoading, isSuccess } =
    useGetConnectionConfigDatasetConfigsQuery(connection!.key);
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

  useEffect(() => {
    if (data && data.items.length) {
      setSelectedDatasetKey(data.items[0].ctl_dataset.fides_key);
    }
  }, [data]);

  const handleCancel = () => {
    router.push(DATASTORE_CONNECTION_ROUTE);
  };

  const handlePatchDatasetConfig = async (
    datasetPairs: DatasetConfigCtlDataset[]
  ) => {
    const params: PatchDatasetsConfigRequest = {
      connection_key: connection?.key as string,
      dataset_pairs: datasetPairs,
    };
    const payload = await patchDatasetConfig(params).unwrap();
    if (payload.failed?.length > 0) {
      errorAlert(payload.failed[0].message);
    } else {
      successAlert("Dataset successfully updated!");
    }
    router.push(DATASTORE_CONNECTION_ROUTE);
  };

  const handleLinkDataset = async () => {
    if (selectedDatasetKey) {
      try {
        let fidesKey = selectedDatasetKey;
        if (data && data.items.length) {
          fidesKey = data.items[0].fides_key;
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
      if (data && data.items.length) {
        const { items: datasetConfigs } = data;
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
    <VStack alignItems="left">
      {loadAllDatasetsError ? (
        <Copy mb={4} color="red">
          There was a problem loading existing datasets, please try again.
        </Copy>
      ) : null}
      <HStack spacing={8} mb={4}>
        {datasetsExist ? (
          <>
            <VStack alignSelf="start" mr={4}>
              <Box data-testid="dataset-selector-section" mb={4}>
                <Copy mb={4}>
                  Choose a dataset to associate with this connector.
                </Copy>
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
            <Copy>or</Copy>
          </>
        ) : null}
        <Box data-testid="yaml-editor-section">
          <Copy mb={4}>View your dataset YAML below!</Copy>
          {isSuccess && data!?.items ? (
            <YamlEditorForm
              data={data.items.map((item) => item.ctl_dataset)}
              isSubmitting={isSubmitting}
              onSubmit={handleSubmitYaml}
              disabled={datasetSelected}
              // Only render the cancel button if the dataset dropdown view is unavailable
              onCancel={!datasetsExist ? handleCancel : undefined}
            />
          ) : null}
        </Box>
      </HStack>
      {datasetsExist ? (
        <Button
          width="fit-content"
          size="sm"
          variant="outline"
          onClick={handleCancel}
        >
          Cancel
        </Button>
      ) : null}
    </VStack>
  );
};

export default DatasetConfiguration;
