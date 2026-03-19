import { Typography } from "fidesui";
import type { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import DataPurposesTable from "~/features/data-purposes/DataPurposesTable";
import useDataPurposesTable from "~/features/data-purposes/useDataPurposesTable";

const DataPurposesPage: NextPage = () => {
  const { error } = useDataPurposesTable();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching data purposes"
      />
    );
  }

  return (
    <Layout title="Data Purposes">
      <PageHeader heading="Data Purposes">
        <Typography.Text>
          Review and manage your data purposes below. Data purposes define the
          reasons data is collected and processed within your organization.
        </Typography.Text>
      </PageHeader>
      <DataPurposesTable />
    </Layout>
  );
};

export default DataPurposesPage;
