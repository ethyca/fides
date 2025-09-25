import {
  AntButton as Button,
  AntTabsProps as TabsProps,
  Box,
  Flex,
  Spacer,
  useDisclosure,
} from "fidesui";
import { useMemo } from "react";

import { ReadOnlyNonEmptyArray, ValueOf } from "~/features/common/utils/array";
import MonitorConfigTab from "~/features/integrations/configure-monitor/MonitorConfigTab";
import DatahubDataSyncTab from "~/features/integrations/configure-scan/DatahubDataSyncTab";
import TaskConditionsTab from "~/features/integrations/configure-tasks/TaskConditionsTab";
import TaskConfigTab from "~/features/integrations/configure-tasks/TaskConfigTab";
import ConfigureIntegrationModal from "~/features/integrations/ConfigureIntegrationModal";
import ConnectionStatusNotice, {
  ConnectionStatusData,
} from "~/features/integrations/ConnectionStatusNotice";
import { ConnectionSystemTypeMap, IntegrationFeature } from "~/types/api";

export type FeatureTabKeys =
  | "connection"
  | "details"
  | "conditions"
  | "manual-tasks"
  | "data-sync"
  | "data-discovery";

export const FEATURE_TAB_KEYS: ReadOnlyNonEmptyArray<FeatureTabKeys> = [
  "connection",
  "details",
  "conditions",
  "manual-tasks",
  "data-sync",
  "data-discovery",
];

type FeatureTab = ValueOf<NonNullable<TabsProps["items"]>> & {
  key: FeatureTabKeys;
};

interface UseFeatureBasedTabsProps {
  connection: any;
  enabledFeatures?: IntegrationFeature[];
  integrationOption?: ConnectionSystemTypeMap;
  testData: ConnectionStatusData;
  needsAuthorization: boolean;
  handleAuthorize: () => void;
  testConnection: () => void;
  testIsLoading: boolean;
  description?: React.ReactNode;
  overview?: React.ReactNode;
  instructions?: React.ReactNode;
  supportsConnectionTest: boolean;
}

export const useFeatureBasedTabs = ({
  connection,
  enabledFeatures,
  integrationOption,
  testData,
  needsAuthorization,
  handleAuthorize,
  testConnection,
  testIsLoading,
  description,
  overview,
  instructions,
  supportsConnectionTest,
}: UseFeatureBasedTabsProps) => {
  const { onOpen, isOpen, onClose } = useDisclosure();

  const tabs = useMemo(() => {
    // Don't show tabs until enabledFeatures is loaded
    // if (!enabledFeatures || !enabledFeatures.length) {
    //   return [];
    // }

    const CONNECTION_TAB = {
      label: "Connection",
      key: "connection",
      children: (
        <Box>
          {supportsConnectionTest && (
            <Flex
              borderRadius="md"
              outline="1px solid"
              outlineColor="gray.100"
              align="center"
              p={3}
            >
              <Flex flexDirection="column">
                <ConnectionStatusNotice
                  testData={testData}
                  connectionOption={integrationOption}
                />
              </Flex>
              <Spacer />
              <div className="flex gap-4">
                {needsAuthorization && (
                  <Button
                    onClick={handleAuthorize}
                    data-testid="authorize-integration-btn"
                  >
                    Authorize integration
                  </Button>
                )}
                {!needsAuthorization && (
                  <Button
                    onClick={testConnection}
                    loading={testIsLoading}
                    data-testid="test-connection-btn"
                  >
                    Test connection
                  </Button>
                )}
                <Button onClick={onOpen} data-testid="manage-btn">
                  Manage
                </Button>
              </div>
            </Flex>
          )}
          <ConfigureIntegrationModal
            isOpen={isOpen}
            onClose={onClose}
            connection={connection}
            description={description}
          />
          {overview}
          {instructions}
        </Box>
      ),
    } as const;

    const DETAILS_TAB: FeatureTab = {
      label: "Details",
      key: "details",
      children: (
        <Box>
          <Flex>
            <Button onClick={onOpen} data-testid="manage-btn">
              Edit integration
            </Button>
          </Flex>

          <ConfigureIntegrationModal
            isOpen={isOpen}
            onClose={onClose}
            connection={connection}
            description={description}
          />
          {overview}
          {instructions}
        </Box>
      ),
    } as const;
    const DATA_SYNC_TAB: FeatureTab = {
      label: "Data sync",
      key: "data-sync",
      children: <DatahubDataSyncTab integration={connection} />,
    } as const;

    const DATA_DISCOVERY_TAB: FeatureTab = {
      label: "Data discovery",
      key: "data-discovery",
      children: (
        <MonitorConfigTab
          integration={connection}
          integrationOption={integrationOption}
        />
      ),
    } as const;

    const TASKS_TAB: FeatureTab = {
      label: "Manual tasks",
      key: "manual-tasks",
      children: <TaskConfigTab integration={connection} />,
    } as const;

    const CONDITIONS_TAB: FeatureTab = {
      label: "Conditions",
      key: "conditions",
      children: <TaskConditionsTab connectionKey={connection?.key} />,
    } as const;

    const tabItems = [
      // const tabItems: ReadOnlyNonEmptyArray<FeatureTab> = [
      enabledFeatures?.includes(IntegrationFeature.WITHOUT_CONNECTION)
        ? DETAILS_TAB
        : CONNECTION_TAB,
      ...(enabledFeatures?.includes(IntegrationFeature.DATA_SYNC)
        ? [DATA_SYNC_TAB]
        : []),
      ...(enabledFeatures?.includes(IntegrationFeature.DATA_DISCOVERY)
        ? [DATA_DISCOVERY_TAB]
        : []),
      ...(enabledFeatures?.includes(IntegrationFeature.TASKS)
        ? [TASKS_TAB]
        : []),
      ...(enabledFeatures?.includes(IntegrationFeature.CONDITIONS)
        ? [CONDITIONS_TAB]
        : []),
    ] as const;

    // Show Details tab for integrations without connection, Connection tab for others
    return tabItems;
  }, [
    connection,
    enabledFeatures,
    integrationOption,
    testData,
    needsAuthorization,
    handleAuthorize,
    testConnection,
    testIsLoading,
    onOpen,
    isOpen,
    onClose,
    description,
    overview,
    instructions,
    supportsConnectionTest,
  ]);

  return tabs;
};
