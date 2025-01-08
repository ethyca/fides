import { useAlert, useAPIHelper } from "common/hooks";
import { selectConnectionTypeState } from "connection-type/connection-type.slice";
import {
  useGetConnectionConfigDatasetConfigsQuery,
  usePatchDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import {
  AntButton as Button,
  AntDivider as Divider,
  AntSelect as Select,
  Box,
  Center,
  HStack,
  Spinner,
  Text,
  TextProps,
  VStack,
} from "fidesui";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

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

const DatasetConfiguration = () => {
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

  const handlePatchDatasetConfig = async (
    datasetPairs: DatasetConfigCtlDataset[],
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
    <VStack alignItems="left" gap={4}>
      {loadAllDatasetsError && (
        <Copy color="red">
          There was a problem loading existing datasets, please try again.
        </Copy>
      )}
      <VStack alignItems="flex-start">
        {datasetsExist && (
          <div>
            <VStack alignSelf="start" gap={4}>
              <Box data-testid="dataset-selector-section">
                <Copy mb={4}>
                  Choose a dataset to associate with this connector.
                </Copy>
                <HStack>
                  <Select
                    allowClear
                    options={allDatasets.map((ds) => ({
                      label: ds.fides_key,
                      value: ds.fides_key,
                    }))}
                    className="w-full"
                    placeholder="Select"
                    onChange={(value) => setSelectedDatasetKey(value)}
                    value={selectedDatasetKey}
                    data-testid="dataset-selector"
                  />
                  <Button
                    onClick={handleLinkDataset}
                    type="primary"
                    className="self-start"
                    disabled={!datasetSelected}
                    data-testid="save-dataset-link-btn"
                  >
                    Save
                  </Button>
                </HStack>
              </Box>
            </VStack>
          </div>
        )}
        {datasetsExist && isSuccess && data!?.items && (
          <Divider plain>or</Divider>
        )}
        {isSuccess && data!?.items && (
          <Box data-testid="yaml-editor-section">
            <Copy mb={4}>View your dataset YAML below!</Copy>
            <YamlEditorForm
              data={data.items.map((item) => item.ctl_dataset)}
              isSubmitting={isSubmitting}
              onSubmit={handleSubmitYaml}
              disabled={datasetSelected}
            />
          </Box>
        )}
      </VStack>
    </VStack>
  );
};

export default DatasetConfiguration;
