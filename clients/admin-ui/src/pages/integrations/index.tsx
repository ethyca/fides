import { Text } from "@fidesui/react";
import { NextPage } from "next";
import NextLink from "next/link";

import { INTEGRATION_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";

const IntegrationListView: NextPage = () => (
  <Text>
    integration list view coming soon;{" "}
    <NextLink href={`${INTEGRATION_MANAGEMENT_ROUTE}/bigquery_connection_1`}>
      click here to go to detail view page
    </NextLink>
  </Text>
);

export default IntegrationListView;
