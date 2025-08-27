import { Box } from "fidesui";
import type { NextPage } from "next";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import SystemsTable from "~/features/system/SystemsTable";

const Systems: NextPage = () => {
  return (
    <FixedLayout title="System inventory">
      <Box data-testid="system-management">
        <PageHeader
          heading="System inventory"
          breadcrumbItems={[{ title: "All systems" }]}
        />
        <SystemsTable />
      </Box>
    </FixedLayout>
  );
};

export default Systems;
