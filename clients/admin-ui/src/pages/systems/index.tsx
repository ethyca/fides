import type { NextPage } from "next";
import React from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import AddSystemsMenu from "~/features/system/AddSystemsMenu";
import SystemsTable from "~/features/system/SystemsTable";
import useSystemsTable from "~/features/system/table/useSystemsTable";

const Systems: NextPage = () => {
  const { error } = useSystemsTable();

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
        <SidePanel.Actions>
          <AddSystemsMenu />
        </SidePanel.Actions>
      </SidePanel>
      <Layout title="System inventory">
        <SystemsTable />
      </Layout>
    </>
  );
};

export default Systems;
