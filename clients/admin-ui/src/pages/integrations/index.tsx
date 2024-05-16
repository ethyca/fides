import { Box, Flex, Button, Spinner, Text } from "@fidesui/react";
import type { NextPage } from "next";
import NextLink from "next/link";
import React from "react";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import IntegrationBox  from "~/features/integrations/IntegrationBox";
import NoIntegrations  from "~/features/integrations/NoIntegrations";



// This is a WIP file
const IntegrationsTabs : NextPage = (props) => {
  return (
    <Box data-testid="integrations">
      {/*<IntegrationBox/>*/}
      <NoIntegrations/>
    </Box>
  );
};

const IntegrationListView: NextPage = () => {
  // const { isLoading, systems } = useSystemsData();
  const isLoading = false;

  return (
    <Layout title="Integrations" mainProps={{ paddingTop: 0 }}>
      <NextLink href={`${INTEGRATION_MANAGEMENT_ROUTE}/bigquery_connection_1`}>
        WIP: click here to go to detail view page
      </NextLink>
      <PageHeader breadcrumbs={[{ title: "Integrations" }]} />
      {isLoading ? <Spinner /> : <IntegrationsTabs/>}
    </Layout>
  );
};

export default IntegrationListView;
