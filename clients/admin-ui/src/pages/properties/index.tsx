import type { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import PropertiesTable from "~/features/properties/PropertiesTable";
import usePropertiesTable from "~/features/properties/usePropertiesTable";

const PropertiesPage: NextPage = () => {
  const { error, searchQuery, updateSearch } = usePropertiesTable();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching properties"
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Properties"
          description="Review and manage your properties. Properties are locations configured for consent management such as a website or mobile app."
        />
        <SidePanel.Search
          onSearch={updateSearch}
          value={searchQuery ?? ""}
          onChange={(e) => updateSearch(e.target.value)}
          placeholder="Search properties..."
        />
      </SidePanel>
      <Layout title="Properties">
        <PropertiesTable searchQuery={searchQuery} onSearchChange={updateSearch} />
      </Layout>
    </>
  );
};

export default PropertiesPage;
