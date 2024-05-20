import { Spinner, Button, Box } from "fidesui";
import type { NextPage } from "next";
import React from "react";
import Layout from "~/features/common/Layout";
import IntegrationsTabs  from "~/features/integrations/IntegrationsTabs";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import DataTabsHeader from "~/features/common/DataTabsHeader";
import { Heading } from "fidesui";
import {
  LinkIcon,
} from "fidesui";

const TABS = [
  {
    label: "All"
  },
  {
    label: "Cloud"
  },
  {
    label: "IDP"
  },
  {
    label: "CRM"
  },
  {
    label: "Database"
  },
  {
    label: "Data Warehouse"
  },
];


const IntegrationListView: NextPage = () => {
  const {
    data,
    isLoading,
  } = useGetAllDatastoreConnectionsQuery({"connection_type": ["bigquery"]});


  const onTabChange = () =>
    console.log(arguments)

  const renderAddIntegrationButton = () =>
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
          onClick={() => {}}
        >
          Add Integration
          <LinkIcon marginLeft="8px"/>
        </Button>
      </Box>

  return (
    <Layout title="Integrations">
      <Heading mb={2} fontSize="2xl" fontWeight="semibold">
        Integrations
      </Heading>
      <Box data-testid="integation-tabs" display="flex">
        <DataTabsHeader
          border="full-width"
          isManual
          onChange={onTabChange}
          data={TABS}
          flexGrow={1}/>
        {renderAddIntegrationButton()}
      </Box>
      {isLoading ? <Spinner /> : <IntegrationsTabs data={data}/>}
    </Layout>
  );
};

export default IntegrationListView;
