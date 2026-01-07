import { Box } from "fidesui";
import type { NextPage } from "next";
import React from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
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
    <Layout title="System inventory" mainProps={{ w: "calc(100vw - 240px)" }}>
      <Box data-testid="system-management">
        <PageHeader
          heading="System inventory"
          breadcrumbItems={[{ title: "All systems" }]}
          rightContent={<AddSystemsMenu />}
          isSticky={false}
        />
        <SystemsTable />
      </Box>
    </Layout>
  );
};

export default Systems;
