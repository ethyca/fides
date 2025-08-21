import { Box } from "fidesui";
import type { NextPage } from "next";
import React from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import NewTable from "~/pages/systems/new-table";
const Systems: NextPage = () => {
  return (
    <Layout title="System inventory">
      <Box data-testid="system-management">
        <PageHeader
          heading="System inventory"
          breadcrumbItems={[{ title: "All systems" }]}
        />
        <NewTable />
      </Box>
    </Layout>
  );
};

export default Systems;
