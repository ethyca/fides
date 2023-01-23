import { Box, Center, Spinner, VStack } from "@fidesui/react";
import { useAlert, useAPIHelper } from "common/hooks";
import { selectConnectionTypeState } from "connection-type/connection-type.slice";
import {
  useGetDatasetsQuery,
  usePatchDatasetMutation,
} from "datastore-connections/datastore-connection.slice";
import { PatchDatasetsRequest } from "datastore-connections/types";
import { useRouter } from "next/router";
import React, { useState } from "react";
import { DATASTORE_CONNECTION_ROUTE } from "src/constants";

import { useAppSelector } from "~/app/hooks";

import YamlEditorForm from "./forms/YamlEditorForm";

const DatasetConfiguration: React.FC = () => {
  const router = useRouter();
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { connection } = useAppSelector(selectConnectionTypeState);
  const { data, isFetching, isLoading, isSuccess } = useGetDatasetsQuery(
    connection!.key
  );
  const [patchDataset] = usePatchDatasetMutation();

  const handleSubmit = async (value: any) => {
    try {
      setIsSubmitting(true);
      const params: PatchDatasetsRequest = {
        connection_key: connection?.key as string,
        datasets: Array.isArray(value) ? value : [value],
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
        View your system yaml below!
      </Box>
      {(isFetching || isLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {isSuccess && data!?.items ? (
        <YamlEditorForm
          data={data.items}
          isSubmitting={isSubmitting}
          onSubmit={handleSubmit}
        />
      ) : null}
    </VStack>
  );
};

export default DatasetConfiguration;
