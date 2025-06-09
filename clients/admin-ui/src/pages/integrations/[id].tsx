import {
  AntButton as Button,
  AntTabs,
  AntTabsProps,
  Box,
  Flex,
  Spacer,
  Spinner,
  useDisclosure,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";
import useTestConnection from "~/features/datastore-connections/useTestConnection";
import getIntegrationTypeInfo, {
  SUPPORTED_INTEGRATIONS,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import MonitorConfigTab from "~/features/integrations/configure-monitor/MonitorConfigTab";
import DatahubDataSyncTab from "~/features/integrations/configure-scan/DatahubDataSyncTab";
import ConfigureIntegrationModal from "~/features/integrations/ConfigureIntegrationModal";
import ConnectionStatusNotice from "~/features/integrations/ConnectionStatusNotice";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import { IntegrationFeatureEnum } from "~/features/integrations/IntegrationFeatureEnum";
import SharedConfigModal from "~/features/integrations/SharedConfigModal";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";
import { ConnectionType } from "~/types/api";

const IntegrationDetailView: NextPage = () => {
  const { query } = useRouter();
  const id = Array.isArray(query.id) ? query.id[0] : query.id;
  const { data: connection, isLoading: integrationIsLoading } =
    useGetDatastoreConnectionByKeyQuery(id ?? "");

  const integrationOption = useIntegrationOption(connection?.connection_type);

  const {
    testConnection,
    isLoading: testIsLoading,
    testData,
  } = useTestConnection(connection);

  const { onOpen, isOpen, onClose } = useDisclosure();

  const { overview, instructions, description, enabledFeatures } =
    getIntegrationTypeInfo(connection?.connection_type);

  const router = useRouter();
  if (
    !!connection &&
    !SUPPORTED_INTEGRATIONS.includes(connection.connection_type)
  ) {
    router.push(INTEGRATION_MANAGEMENT_ROUTE);
  }

  const supportsConnectionTest =
    connection?.connection_type !== ConnectionType.MANUAL_WEBHOOK;

  const tabs: AntTabsProps["items"] = [];

  // Show Details tab for integrations without connection, Connection tab for others
  if (enabledFeatures?.includes(IntegrationFeatureEnum.WITHOUT_CONNECTION)) {
    tabs.push({
      label: "Details",
      key: "details",
      children: (
        <Box maxW="720px">
          <Flex>
            <Button onClick={onOpen} data-testid="manage-btn">
              Edit integration
            </Button>
          </Flex>

          <ConfigureIntegrationModal
            isOpen={isOpen}
            onClose={onClose}
            connection={connection!}
            description={description}
          />
          {overview}
          {instructions}
        </Box>
      ),
    });
  } else {
    tabs.push({
      label: "Connection",
      key: "connection",
      children: (
        <Box maxW="720px">
          {supportsConnectionTest && (
            <Flex
              borderRadius="md"
              outline="1px solid"
              outlineColor="gray.100"
              align="center"
              p={3}
            >
              <Flex flexDirection="column">
                <ConnectionStatusNotice testData={testData} />
              </Flex>
              <Spacer />
              <div className="flex gap-4">
                <Button
                  onClick={testConnection}
                  loading={testIsLoading}
                  data-testid="test-connection-btn"
                >
                  Test connection
                </Button>
                <Button onClick={onOpen} data-testid="manage-btn">
                  Manage
                </Button>
              </div>
            </Flex>
          )}
          {!supportsConnectionTest && (
            <Flex>
              <Button onClick={onOpen} data-testid="manage-btn">
                Edit integration
              </Button>
            </Flex>
          )}

          <ConfigureIntegrationModal
            isOpen={isOpen}
            onClose={onClose}
            connection={connection!}
            description={description}
          />
          {overview}
          {instructions}
        </Box>
      ),
    });
  }

  // Add conditional tabs based on enabled features
  if (enabledFeatures?.includes(IntegrationFeatureEnum.DATA_SYNC)) {
    tabs.push({
      label: "Data sync",
      key: "data-sync",
      children: <DatahubDataSyncTab integration={connection!} />,
    });
  }

  if (enabledFeatures?.includes(IntegrationFeatureEnum.DATA_DISCOVERY)) {
    tabs.push({
      label: "Data discovery",
      key: "data-discovery",
      children: (
        <MonitorConfigTab
          integration={connection!}
          integrationOption={integrationOption}
        />
      ),
    });
  }

  return (
    <Layout title="Integrations">
      <PageHeader
        heading="Integrations"
        breadcrumbItems={[
          {
            title: "All integrations",
            href: INTEGRATION_MANAGEMENT_ROUTE,
          },
          {
            title: connection?.name ?? connection?.key ?? "",
          },
        ]}
      >
        <SharedConfigModal />
        <IntegrationBox integration={connection} showDeleteButton />
        {integrationIsLoading ? (
          <Spinner />
        ) : (
          !!connection && <AntTabs items={tabs} />
        )}
      </PageHeader>
    </Layout>
  );
};

export default IntegrationDetailView;
