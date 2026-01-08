import { Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { PropertiesTable } from "~/features/properties/PropertiesTable";

const PropertiesPage: NextPage = () => (
  <Layout title="Properties">
    <PageHeader heading="Properties">
      <Typography.Text>
        Review and manage your properties below. Properties are the locations
        you have configured for consent management such as a website or mobile
        app.
      </Typography.Text>
    </PageHeader>
    <PropertiesTable />
  </Layout>
);

export default PropertiesPage;
