import Layout from "common/Layout";
import { Box } from "fidesui";
import type { NextPage } from "next";
import React from "react";

import PageHeader from "~/features/common/PageHeader";
import { CustomFieldsTable } from "~/features/custom-fields/CustomFieldsTable";

const CustomFields: NextPage = () => (
  <Layout title="Custom fields">
    <Box data-testid="custom-fields-management">
      <PageHeader heading="Custom fields" />
      <CustomFieldsTable />
    </Box>
  </Layout>
);
export default CustomFields;
