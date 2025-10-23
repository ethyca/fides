import { Box } from "fidesui";
import type { NextPage } from "next";
import React from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import AddSystemsMenu from "~/features/system/AddSystemsMenu";
import SystemsTable from "~/features/system/SystemsTable";

const Systems: NextPage = () => {
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
