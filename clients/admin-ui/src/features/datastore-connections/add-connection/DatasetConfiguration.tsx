import { Box, Center, Spinner, VStack } from "@fidesui/react";
import { useAppSelector } from "app/hooks";
import { useAlert, useAPIHelper } from "common/hooks";
import { selectConnectionTypeState } from "connection-type/connection-type.slice";
import {
  useGetDatasetsQuery,
  usePatchDatasetMutation,
} from "datastore-connections/datastore-connection.slice";
import { PatchDatasetsRequest } from "datastore-connections/types";
import { useRouter } from "next/router";
import React, { useEffect, useRef, useState } from "react";
import { DATASTORE_CONNECTION_ROUTE } from "src/constants";

import YamlEditorForm from "./forms/YamlEditorForm";
import { replaceURL } from "./helpers";

const DatasetConfiguration: React.FC = () => {
  const mounted = useRef(false);
  const router = useRouter();
  const { errorAlert, successAlert } = useAlert();
  const { handleError } = useAPIHelper();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { connection, step } = useAppSelector(selectConnectionTypeState);
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

  useEffect(() => {
    mounted.current = true;
    if (connection?.key) {
      replaceURL(connection.key, step.href);
    }
    return () => {
      mounted.current = false;
    };
  }, [connection?.key, step.href]);

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
          data={data.items}
          isSubmitting={isSubmitting}
          onSubmit={handleSubmit}
        />
      ) : null}
    </VStack>
  );
};

export default DatasetConfiguration;
