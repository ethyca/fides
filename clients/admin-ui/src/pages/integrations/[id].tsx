import { Box, Button, Flex, Spacer, Spinner, useDisclosure } from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import DataTabs, { TabData } from "~/features/common/DataTabs";
import Layout from "~/features/common/Layout";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";
import BigQueryOverview from "~/features/integrations/bigqueryOverviewCopy";
import ConfigureIntegrationModal from "~/features/integrations/ConfigureIntegrationModal";
import ConnectionStatusNotice from "~/features/integrations/ConnectionStatusNotice";
import IntegrationBox from "~/features/integrations/IntegrationBox";

const IntegrationDetailView: NextPage = () => {
  const { query } = useRouter();
  const id = Array.isArray(query.id) ? query.id[0] : query.id;
  const { data: connection, isLoading } = useGetDatastoreConnectionByKeyQuery(
    id ?? ""
  );

  const { onOpen, isOpen, onClose } = useDisclosure();
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
              <ConnectionStatusNotice
                timestamp={connection?.last_test_timestamp}
                succeeded={connection?.last_test_succeeded}
              />
            </Flex>
            <Spacer />
            <Button variant="outline" onClick={onOpen}>
              Manage connection
            </Button>
          </Flex>
          <ConfigureIntegrationModal
            isOpen={isOpen}
            onClose={onClose}
            connection={connection!}
          />
          <BigQueryOverview />
        </Box>
      ),
    },
    // {
    //   label: "Data discovery",
    //   content: <Text>[insert discovery tab here]</Text>,
    // },
  ];

  return (
    <Layout title="Integrations">
      <PageHeader
        breadcrumbs={[
          {
            title: "Integrations",
            link: INTEGRATION_MANAGEMENT_ROUTE,
          },
          {
            title: id ?? "",
          },
        ]}
      >
        <IntegrationBox integration={connection} />
        {isLoading ? <Spinner /> : <DataTabs data={tabs} />}
      </PageHeader>
    </Layout>
  );
};

export default IntegrationDetailView;
