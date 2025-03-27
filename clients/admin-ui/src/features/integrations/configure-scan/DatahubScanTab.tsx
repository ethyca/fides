/* eslint-disable react/no-unstable-nested-components */

import { Text, VStack, Button, Box, useToast } from "fidesui";
import { AntSelect as Select } from "fidesui";
import { useState } from "react";
import { useGetAllFilteredDatasetsQuery } from "~/features/dataset";
import { useSyncDatahubConnectionMutation } from "~/features/plus/plus.slice";
import { successToastParams } from "~/features/common/toast";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
  ConnectionType,
  Dataset,
} from "~/types/api";

const DATAHUB_COPY = `Trigger a manual DataHub sync that will run in the background. This will sync Fides Data Categories into Datahub using Datahub's Glossary Terms. You can select specific datasets to sync, and the process will run asynchronously.`;

const DatahubScanTab = ({
  integration,
  integrationOption,
}: {
  integration: ConnectionConfigurationResponse;
  integrationOption?: ConnectionSystemTypeMap;
}) => {
  const [selectedDatasets, setSelectedDatasets] = useState<string[]>([]);
  const { data: datasets, isLoading } = useGetAllFilteredDatasetsQuery({
    minimal: true,
    connection_type: ConnectionType.BIGQUERY,
  });
  const [syncDatahubConnection] = useSyncDatahubConnectionMutation();
  const toast = useToast();

  const handleSync = async () => {
    try {
      const response = await syncDatahubConnection({
        connectionKey: integration.key,
        datasetIds: selectedDatasets,
      });
      // Clear selection after successful sync
      setSelectedDatasets([]);

      const successCount = response.data?.succeeded.length ?? 0;
      const failedCount = response.data?.failed.length ?? 0;
      const message = `DataHub sync started successfully. ${successCount} dataset(s) queued for sync${failedCount > 0 ? `, ${failedCount} dataset(s) failed` : ''}.`;

      toast(successToastParams(message));
    } catch (error) {
      console.error("Failed to sync datasets:", error);
      // TODO: Add error handling/notification
    }
  };

  const handleSyncAll = async () => {
    if (!datasets?.length) return;

    try {
      const response = await syncDatahubConnection({
        connectionKey: integration.key,
        datasetIds: datasets.map((dataset: Dataset) => dataset.fides_key),
      });

      const successCount = response.data?.succeeded.length ?? 0;
      const failedCount = response.data?.failed.length ?? 0;
      const message = `DataHub sync started successfully. ${successCount} dataset(s) queued for sync${failedCount > 0 ? `, ${failedCount} dataset(s) failed` : ''}.`;

      toast(successToastParams(message));
    } catch (error) {
      console.error("Failed to sync all datasets:", error);
      // TODO: Add error handling/notification
    }
  };

  return (
    <VStack spacing={6} align="stretch">
      <Text maxW="720px" fontSize="sm" data-testid="scan-description">
        {DATAHUB_COPY}
      </Text>

      <Box>
        <Text mb={4} fontSize="sm" fontWeight="medium">
          Select Datasets to Sync
        </Text>
        <Select
          mode="multiple"
          loading={isLoading}
          options={datasets?.map((dataset: Dataset) => ({
            label: dataset.name || dataset.fides_key,
            value: dataset.fides_key,
          }))}
          onChange={(values) => setSelectedDatasets(values)}
          value={selectedDatasets}
          placeholder="Select datasets..."
          className="w-full"
          data-testid="dataset-selector"
        />
      </Box>

      <VStack spacing={4} align="stretch">
        <Button
          colorScheme="primary"
          onClick={handleSync}
          isDisabled={selectedDatasets.length === 0}
          data-testid="sync-button"
        >
          Sync Selected
        </Button>
        <Button
          colorScheme="primary"
          variant="outline"
          onClick={handleSyncAll}
          isDisabled={!datasets?.length || isLoading}
          data-testid="sync-all-button"
        >
          Sync All Datasets
        </Button>
      </VStack>
    </VStack>
  );
};

export default DatahubScanTab;
