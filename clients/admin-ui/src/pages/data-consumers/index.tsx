import type { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useSearch } from "~/features/common/hooks/useSearch";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import { useGetAllDataConsumersQuery } from "~/features/data-consumers/data-consumer.slice";
import DataConsumersTable from "~/features/data-consumers/DataConsumersTable";

const DataConsumersPage: NextPage = () => {
  const { error } = useGetAllDataConsumersQuery({});
  const { searchQuery, updateSearch } = useSearch();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching data consumers"
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Data consumers"
          description="Review and manage your data consumers below. Data consumers represent the services, applications, groups, or users that access personal data."
        />
        <SidePanel.Search
          onSearch={updateSearch}
          value={searchQuery ?? ""}
          onChange={(e) => updateSearch(e.target.value)}
          placeholder="Search data consumers..."
        />
      </SidePanel>
      <Layout title="Data consumers">
        <DataConsumersTable searchQuery={searchQuery} onSearchChange={updateSearch} />
      </Layout>
    </>
  );
};

export default DataConsumersPage;
