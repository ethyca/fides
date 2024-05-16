import { Spinner } from "fidesui";
import type { NextPage } from "next";
import React from "react";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import IntegrationsTabs  from "~/features/integrations/IntegrationsTabs";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";

const IntegrationListView: NextPage = () => {
  const {
    data,
    isLoading,
  } = useGetAllDatastoreConnectionsQuery({"connection_type": ["bigquery"]});

  return (
    <Layout title="Integrations" mainProps={{ paddingTop: 0 }}>
      <PageHeader breadcrumbs={[{ title: "Integrations" }]} />
      {isLoading ? <Spinner /> : <IntegrationsTabs data={data}/>}
    </Layout>
  );
};

export default IntegrationListView;
