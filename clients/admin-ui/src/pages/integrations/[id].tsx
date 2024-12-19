import {
  AntButton as Button,
  Box,
  Flex,
  Spacer,
  Spinner,
  useDisclosure,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import DataTabs, { TabData } from "~/features/common/DataTabs";
import Layout from "~/features/common/Layout";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";
import useTestConnection from "~/features/datastore-connections/useTestConnection";
import getIntegrationTypeInfo, {
  SUPPORTED_INTEGRATIONS,
} from "~/features/integrations/add-integration/allIntegrationTypes";
import MonitorConfigTab from "~/features/integrations/configure-monitor/MonitorConfigTab";
import ConfigureIntegrationModal from "~/features/integrations/ConfigureIntegrationModal";
import ConnectionStatusNotice from "~/features/integrations/ConnectionStatusNotice";
import IntegrationBox from "~/features/integrations/IntegrationBox";
import useIntegrationOption from "~/features/integrations/useIntegrationOption";

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

  const { overview, instructions } = getIntegrationTypeInfo(
    connection?.connection_type,
  );

  const router = useRouter();
  if (
    !!connection &&
    !SUPPORTED_INTEGRATIONS.includes(connection.connection_type)
  ) {
    router.push(INTEGRATION_MANAGEMENT_ROUTE);
  }

  const tabs: TabData[] = [
    {
      label: "Connection",
      content: (
        <Box maxW="720px">
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
          <ConfigureIntegrationModal
            isOpen={isOpen}
            onClose={onClose}
            connection={connection!}
          />
          {overview}
          {instructions}
        </Box>
      ),
    },
    {
      label: "Data discovery",
      content: (
        <MonitorConfigTab
          integration={connection!}
          integrationOption={integrationOption}
        />
      ),
    },
  ];

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
        <IntegrationBox integration={connection} showDeleteButton />
        {integrationIsLoading ? (
          <Spinner />
        ) : (
          !!connection && <DataTabs data={tabs} isLazy />
        )}
      </PageHeader>
    </Layout>
  );
};

export default IntegrationDetailView;
