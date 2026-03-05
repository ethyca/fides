import { Typography } from "fidesui";
import type { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import PropertiesTable from "~/features/properties/PropertiesTable";
import usePropertiesTable from "~/features/properties/usePropertiesTable";

const PropertiesPage: NextPage = () => {
  const { error } = usePropertiesTable();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching properties"
      />
    );
  }

  return (
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
};

export default PropertiesPage;
