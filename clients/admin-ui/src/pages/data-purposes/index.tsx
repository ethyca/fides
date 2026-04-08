import type { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import { useGetAllDataPurposesQuery } from "~/features/data-purposes/data-purpose.slice";
import DataPurposesTable from "~/features/data-purposes/DataPurposesTable";

const DataPurposesPage: NextPage = () => {
  const { error } = useGetAllDataPurposesQuery({});

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching data purposes"
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Data Purposes"
          description="Review and manage your data purposes below. Data purposes define the reasons data is collected and processed within your organization."
        />
      </SidePanel>
      <Layout title="Data Purposes">
        <DataPurposesTable />
      </Layout>
    </>
  );
};

export default DataPurposesPage;
