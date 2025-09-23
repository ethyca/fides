import Layout from "common/Layout";
import { AntTypography, Box } from "fidesui";
import type { NextPage } from "next";
import React from "react";

import PageHeader from "~/features/common/PageHeader";
import { CustomFieldsTableV2 } from "~/features/custom-fields/CustomFieldsTableV2";

const CUSTOM_FIELDS_COPY =
  "Custom fields provide organizations with the capability to capture metrics that are unique to their specific needs, allowing them to create customized reports. These fields can be added to either systems or elements within a taxonomy, and once added, they become reportable fields that are visible on the data map.";

const CustomFields: NextPage = () => (
  <Layout title="Custom fields">
    <Box data-testid="custom-fields-management">
      <PageHeader heading="Custom fields">
        <AntTypography.Paragraph className="max-w-screen-md">
          {CUSTOM_FIELDS_COPY}
        </AntTypography.Paragraph>
      </PageHeader>
      <CustomFieldsTableV2 />
    </Box>
  </Layout>
);
export default CustomFields;
