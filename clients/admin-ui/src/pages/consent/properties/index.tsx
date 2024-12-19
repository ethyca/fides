import { Text } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { PropertiesTable } from "~/features/properties/PropertiesTable";

const PropertiesPage: NextPage = () => (
  <Layout title="Properties">
    <PageHeader heading="Properties">
      <Text fontSize="sm" width={{ base: "100%", lg: "60%" }}>
        Review and manage your properties below. Properties are the locations
        you have configured for consent management such as a website or mobile
        app.
      </Text>
    </PageHeader>
    <PropertiesTable />
  </Layout>
);

export default PropertiesPage;
