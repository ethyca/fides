import { Box, Heading } from "@fidesui/react";
import Layout from "common/Layout";
import type { NextPage } from "next";
import React from "react";

import { CustomFieldsTable } from "~/features/custom-fields/CustomFieldsTable";

const CustomFields: NextPage = () => (
  <Layout title="Custom fields">
    <Box data-testid="custom-fields-management">
      <Heading marginBottom={4} fontSize="2xl">
        Manage custom fields
      </Heading>
      <CustomFieldsTable />
    </Box>
  </Layout>
);
export default CustomFields;
