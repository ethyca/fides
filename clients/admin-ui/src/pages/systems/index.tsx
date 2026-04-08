import type { NextPage } from "next";
import React from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import AddSystemsMenu from "~/features/system/AddSystemsMenu";
import SystemsTable from "~/features/system/SystemsTable";
import useSystemsTable from "~/features/system/table/useSystemsTable";

const Systems: NextPage = () => {
  const { error, searchQuery, updateSearch } = useSystemsTable();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your systems"
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="System inventory"
          breadcrumbItems={[{ title: "All systems" }]}
        />
        <SidePanel.Search
          onSearch={updateSearch}
          value={searchQuery ?? ""}
          onChange={(e) => updateSearch(e.target.value)}
          placeholder="Search systems..."
        />
        <SidePanel.Actions>
          <AddSystemsMenu />
        </SidePanel.Actions>
      </SidePanel>
      <Layout title="System inventory">
        <SystemsTable searchQuery={searchQuery} onSearchChange={updateSearch} />
      </Layout>
    </>
  );
};

export default Systems;
