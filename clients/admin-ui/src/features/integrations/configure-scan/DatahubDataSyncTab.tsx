/* eslint-disable react/no-unstable-nested-components */

import { Button, Link, Text, useToast, VStack } from "fidesui";
import { useState } from "react";

import { successToastParams } from "~/features/common/toast";
import { useGetAllFilteredDatasetsQuery } from "~/features/dataset";
import { useGetConnectionConfigDatasetConfigsQuery } from "~/features/datastore-connections";
import { useSyncDatahubConnectionMutation } from "~/features/plus/plus.slice";
import { ConnectionConfigurationResponse, ConnectionType } from "~/types/api";

const DATAHUB_COPY_1 = `If you're using DataHub for metadata management, select sync datasets to push data categories from Fides to your DataHub datasets.`;

const DATAHUB_COPY_2 = `Fides assigns data categories to datasets based on your privacy taxonomy. With this integration, those categories can be added as glossary terms to matching datasets in DataHub-keeping your labeling consistent across systems. To learn more about our DataHub integration, view our docs `;

const DatahubDataSyncTab = ({
  integration,
}: {
  integration: ConnectionConfigurationResponse;
}) => {
  const { data: datasetConfigs } = useGetConnectionConfigDatasetConfigsQuery(
    integration.key,
  );
  const { data: bigqueryDatasets } = useGetAllFilteredDatasetsQuery({
    minimal: true,
    connection_type: ConnectionType.BIGQUERY,
  });
  const [syncDatahubConnection, { isLoading }] =
    useSyncDatahubConnectionMutation();
  const toast = useToast();
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    try {
      setIsSyncing(true);
      const configuredDatasetIds =
        datasetConfigs?.items?.map((config) => config.fides_key) ?? [];
      const bigqueryDatasetIds =
        bigqueryDatasets?.map((dataset) => dataset.fides_key) ?? [];

      // Use configured datasets if available, otherwise fall back to all BigQuery datasets
      const datasetIds =
        configuredDatasetIds.length > 0
          ? configuredDatasetIds
          : bigqueryDatasetIds;

      const response = await syncDatahubConnection({
        connectionKey: integration.key,
        datasetIds,
      });

      const successCount = response.data?.succeeded.length ?? 0;
      const message = `Fides has begun syncing with DataHub. There ${successCount === 1 ? "is" : "are"} ${successCount} dataset${successCount === 1 ? "" : "s"} queued for syncing.`;

      toast(successToastParams(message));
    } catch (error) {
      toast({
        title: "Error syncing datasets",
        description:
          "There was an error syncing your datasets with DataHub. Please try again.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <VStack spacing={6} align="stretch">
      <VStack spacing={4} align="stretch">
        <Text maxW="720px" fontSize="sm" data-testid="scan-description-1">
          {DATAHUB_COPY_1}
        </Text>
        <Text maxW="720px" fontSize="sm" data-testid="scan-description-2">
          {DATAHUB_COPY_2}
          <Link
            href="https://ethyca.com/docs/user-guides/integrations/saas-integrations/datahub"
            isExternal
            color="blue.500"
            textDecoration="underline"
          >
            here
          </Link>
          .
        </Text>
      </VStack>

      <Button
        colorScheme="primary"
        onClick={handleSync}
        data-testid="sync-button"
        width="fit-content"
        isLoading={isSyncing || isLoading}
        loadingText="Syncing datasets..."
      >
        Sync Datasets
      </Button>
    </VStack>
  );
};

export default DatahubDataSyncTab;
