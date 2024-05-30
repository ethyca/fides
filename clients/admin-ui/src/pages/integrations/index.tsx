import {
  Box,
  Button,
  Heading,
  LinkIcon,
  Spinner,
  useDisclosure,
} from "fidesui";
import type { NextPage } from "next";
import React from "react";

import DataTabsHeader from "~/features/common/DataTabsHeader";
import Layout from "~/features/common/Layout";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import AddIntegrationModal from "~/features/integrations/AddIntegrationModal";
import IntegrationsTabs from "~/features/integrations/IntegrationsTabs";

const TABS = [
  {
    label: "All",
    content: <p />,
  },
];

const IntegrationListView: NextPage = () => {
  const { data, isLoading } = useGetAllDatastoreConnectionsQuery({
    connection_type: ["bigquery"],
  });

  const { onOpen, isOpen, onClose } = useDisclosure();

  return (
    <Layout title="Integrations">
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Integrations
      </Heading>
      <Box data-testid="integration-tabs" display="flex">
        <DataTabsHeader border="full-width" isManual data={TABS} flexGrow={1} />
        <Box
          borderBottom="2px solid"
          borderColor="gray.200"
          height="fit-content"
          pr="2"
          pb="2"
        >
          <Button
            size="sm"
            variant="outline"
            onClick={onOpen}
            data-testid="add-integration-btn"
          >
            Add Integration
            <LinkIcon marginLeft="8px" />
          </Button>
        </Box>
      </Box>
      {isLoading ? (
        <Spinner />
      ) : (
        <IntegrationsTabs
          integrations={data?.items ?? []}
          onOpenAddModal={onOpen}
        />
      )}
      <AddIntegrationModal isOpen={isOpen} onClose={onClose} />
    </Layout>
  );
};

export default IntegrationListView;
