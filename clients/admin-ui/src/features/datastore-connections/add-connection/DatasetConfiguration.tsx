import { Box, Center, Spinner, VStack } from "@fidesui/react";
import { useAlert, useAPIHelper } from "common/hooks";
import { selectConnectionTypeState } from "connection-type/connection-type.slice";
import {
  useGetDatasetConfigsQuery,
  usePatchDatasetConfigsMutation,
} from "datastore-connections/datastore-connection.slice";
import { PatchDatasetsConfigRequest } from "datastore-connections/types";
import { useRouter } from "next/router";
import React, { useState } from "react";
import { DATASTORE_CONNECTION_ROUTE } from "src/constants";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import { useUpsertDatasetsMutation } from "~/features/dataset";
import { Dataset, DatasetConfigCtlDataset } from "~/types/api";

import YamlEditorForm from "./forms/YamlEditorForm";

const DatasetConfiguration: React.FC = () => {
  const router = useRouter();
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { connection } = useAppSelector(selectConnectionTypeState);
  const { data, isFetching, isLoading, isSuccess } = useGetDatasetConfigsQuery(
    connection!.key
  );
  const [patchDataset] = usePatchDatasetConfigsMutation();
  const [upsertDatasets] = useUpsertDatasetsMutation();

  const handleSubmit = async (value: unknown) => {
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

      const params: PatchDatasetsConfigRequest = {
        connection_key: connection?.key as string,
        dataset_pairs: pairs,
      };
      const payload = await patchDataset(params).unwrap();
      if (payload.failed?.length > 0) {
        errorAlert(payload.failed[0].message);
      } else {
        successAlert("Dataset successfully updated!");
      }
      router.push(DATASTORE_CONNECTION_ROUTE);
    } catch (error) {
      handleError(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <VStack align="stretch" flex="1">
      <Box color="gray.700" fontSize="14px" mb={4}>
        View your system yaml below! You can also modify the yaml if you need to
        assign any references between datasets.
      </Box>
      {(isFetching || isLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {isSuccess && data!?.items ? (
        <YamlEditorForm
          data={data.items.map((item) => item.ctl_dataset)}
          isSubmitting={isSubmitting}
          onSubmit={handleSubmit}
        />
      ) : null}
    </VStack>
  );
};

export default DatasetConfiguration;
