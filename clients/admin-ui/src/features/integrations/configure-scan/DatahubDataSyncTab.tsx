/* eslint-disable react/no-unstable-nested-components */

import { Text, VStack, Button, useToast, Link, Spinner } from "fidesui";
import { useGetAllFilteredDatasetsQuery } from "~/features/dataset";
import { useGetConnectionConfigDatasetConfigsQuery } from "~/features/datastore-connections";
import { useSyncDatahubConnectionMutation } from "~/features/plus/plus.slice";
import { successToastParams } from "~/features/common/toast";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
} from "~/types/api";
import { useState } from "react";

const DATAHUB_COPY_1 = `If you're using DataHub for metadata management, select sync datasets to push data categories from Fides to your DataHub datasets.`;

const DATAHUB_COPY_2 = `Fides assigns data categories to datasets based on your privacy taxonomy. With this integration, those categories can be added as glossary terms to matching datasets in DataHub-keeping your labeling consistent across systems. To learn more about our DataHub integration, view our docs `;

const DatahubDataSyncTab = ({
  integration,
  integrationOption,
}: {
  integration: ConnectionConfigurationResponse;
  integrationOption?: ConnectionSystemTypeMap;
}) => {
  const { data: datasetConfigs } = useGetConnectionConfigDatasetConfigsQuery(
    integration.key
  );
  const { data: bigqueryDatasets } = useGetAllFilteredDatasetsQuery({
    minimal: true,
    connection_type: ConnectionType.BIGQUERY,
  });
  const [syncDatahubConnection, { isLoading }] = useSyncDatahubConnectionMutation();
  const toast = useToast();
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    try {
      setIsSyncing(true);
      const configuredDatasetIds = datasetConfigs?.items?.map(config => config.fides_key) ?? [];
      const bigqueryDatasetIds = bigqueryDatasets?.map(dataset => dataset.fides_key) ?? [];

      // Use configured datasets if available, otherwise fall back to all BigQuery datasets
      const datasetIds = configuredDatasetIds.length > 0 ? configuredDatasetIds : bigqueryDatasetIds;

      const response = await syncDatahubConnection({
        connectionKey: integration.key,
        datasetIds,
      });

      const successCount = response.data?.succeeded.length ?? 0;
      const failedCount = response.data?.failed.length ?? 0;
      const message = `DataHub sync started successfully. ${successCount} dataset(s) queued for sync${failedCount > 0 ? `, ${failedCount} dataset(s) failed` : ''}.`;

      toast(successToastParams(message));
    } catch (error) {
      console.error("Failed to sync datasets:", error);
      // TODO: Add error handling/notification
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
