import { Box, Spinner } from "@fidesui/react";
import type { NextPage } from "next";
import React from "react";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import IntegrationBox  from "~/features/integrations/IntegrationBox";
import NoIntegrations  from "~/features/integrations/NoIntegrations";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";


const IntegrationsTabs: NextPage = ({data}) => {
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
  const {
    data,
    isLoading,
  } = useGetAllDatastoreConnectionsQuery({}); // ({"connection_type": "bigquery"});

  return (
    <Layout title="Integrations" mainProps={{ paddingTop: 0 }}>
      <PageHeader breadcrumbs={[{ title: "Integrations" }]} />
      {isLoading ? <Spinner /> : <IntegrationsTabs data={data}/>}
    </Layout>
  );
};

export default IntegrationListView;
