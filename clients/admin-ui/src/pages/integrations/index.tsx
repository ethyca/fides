import { Box, Flex, Button, Spinner, Text } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import React from "react";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import IntegrationBox  from "~/features/integrations/IntegrationBox";
import NoIntegrations  from "~/features/integrations/NoIntegrations";

import {
  useGetAllDatastoreConnectionsQuery,
} from "~/features/datastore-connections/datastore-connection.slice";



// This is a WIP file
const IntegrationsTabs : NextPage = ({data}) => {
  const renderIntegration = (item) =>
    <IntegrationBox key={item.key} integration={item}/>

  const renderNoIntegrations = () =>
    !data.total && (<NoIntegrations/>)

  return (
    <Box data-testid="integrations">
      {data.items.map(renderIntegration)}
      {renderNoIntegrations()}
    </Box>
  );
};

const IntegrationListView: NextPage = () => {
  // const { isLoading, systems } = useSystemsData();
  const {
    data,
    isLoading,
  } = useGetAllDatastoreConnectionsQuery({}); // ({"connection_type": "bigquery"});
  console.log(data)

  return (
    <Layout title="Integrations" mainProps={{ paddingTop: 0 }}>
      <NextLink href={`${INTEGRATION_MANAGEMENT_ROUTE}/bigquery_connection_1`}>
        WIP: click here to go to detail view page
      </NextLink>
      <PageHeader breadcrumbs={[{ title: "Integrations" }]} />
      {isLoading ? <Spinner /> : <IntegrationsTabs data={data}/>}
    </Layout>
  );
};

export default IntegrationListView;
