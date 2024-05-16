import { WarningIcon } from "@chakra-ui/icons";
import {
  Box,
  Button,
  CheckCircleIcon,
  Flex,
  Spacer,
  Spinner,
  Text,
  useDisclosure,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";

import DataTabs, { TabData } from "~/features/common/DataTabs";
import InfoCopy from "~/features/common/InfoCopy";
import Layout from "~/features/common/Layout";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { formatDate } from "~/features/common/utils";
import { useGetDatastoreConnectionByKeyQuery } from "~/features/datastore-connections";
import BIGQUERY_COPY from "~/features/integrations/BigqueryCopy";
import ConfigureIntegrationModal from "~/features/integrations/ConfigureIntegrationModal";

const ConnectionStatusNotice = ({
  timestamp,
  succeeded,
}: {
  timestamp?: string;
  succeeded?: boolean;
}) => {
  if (!timestamp) {
    return <Text>Connection not tested</Text>;
  }
  const testDate = formatDate(timestamp);
  return succeeded ? (
    <Flex color="green.400" align="center">
      <CheckCircleIcon mr={2} />
      <Text>Last connected {testDate}</Text>
    </Flex>
  ) : (
    <Flex color="red.400" align="center">
      <WarningIcon mr={2} />
      <Text>Last connection failed {testDate}</Text>
    </Flex>
  );
};

const IntegrationDetailView: NextPage = () => {
  const { query } = useRouter();
  const id = Array.isArray(query.id) ? query.id[0] : query.id;
  const { data, isLoading } = useGetDatastoreConnectionByKeyQuery(id ?? "");

  const connection = {
    ...data,
    last_test_succeeded: false,
  };

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
          <ConfigureIntegrationModal isOpen={isOpen} onClose={onClose} />
          <InfoCopy info={BIGQUERY_COPY} />
        </Box>
      ),
    },
    {
      label: "Data discovery",
      content: <Text>[insert discovery tab here]</Text>,
    },
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
        {isLoading ? <Spinner /> : <DataTabs data={tabs} />}
      </PageHeader>
    </Layout>
  );
};

export default IntegrationDetailView;
