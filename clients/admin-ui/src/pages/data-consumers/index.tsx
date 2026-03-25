import { Typography } from "fidesui";
import type { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useGetAllDataConsumersQuery } from "~/features/data-consumers/data-consumer.slice";
import DataConsumersTable from "~/features/data-consumers/DataConsumersTable";

const DataConsumersPage: NextPage = () => {
  const { error } = useGetAllDataConsumersQuery({});

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching data consumers"
      />
    );
  }

  return (
    <Layout title="Data consumers">
      <PageHeader heading="Data consumers">
        <Typography.Text>
          Review and manage your data consumers below. Data consumers represent
          the services, applications, groups, or users that access personal
          data.
        </Typography.Text>
      </PageHeader>
      <DataConsumersTable />
    </Layout>
  );
};

export default DataConsumersPage;
