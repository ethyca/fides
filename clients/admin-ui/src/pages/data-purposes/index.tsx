import type { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import { useSearch } from "~/features/common/hooks/useSearch";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import { useGetAllDataPurposesQuery } from "~/features/data-purposes/data-purpose.slice";
import DataPurposesTable from "~/features/data-purposes/DataPurposesTable";

const DataPurposesPage: NextPage = () => {
  const { error } = useGetAllDataPurposesQuery({});
  const { searchQuery, updateSearch } = useSearch();

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
        <SidePanel.Search
          onSearch={updateSearch}
          value={searchQuery ?? ""}
          onChange={(e) => updateSearch(e.target.value)}
          placeholder="Search data purposes..."
        />
      </SidePanel>
      <Layout title="Data Purposes">
        <DataPurposesTable searchQuery={searchQuery} onSearchChange={updateSearch} />
      </Layout>
    </>
  );
};

export default DataPurposesPage;
