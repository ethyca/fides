import Layout from "common/Layout";
import { Typography } from "fidesui";
import type { NextPage } from "next";
import React from "react";

import PageHeader from "~/features/common/PageHeader";
import CustomFieldsTable from "~/features/custom-fields/CustomFieldsTable";

const CUSTOM_FIELDS_COPY =
  "Custom fields provide organizations with the capability to capture metrics that are unique to their specific needs, allowing them to create customized reports. These fields can be added to either systems or elements within a taxonomy, and once added, they become reportable fields that are visible on the data map.";

const CustomFields: NextPage = () => (
  <Layout title="Custom fields">
    <PageHeader heading="Custom fields" isSticky={false} className="pb-0">
      <Typography.Paragraph className="max-w-screen-md">
        {CUSTOM_FIELDS_COPY}
      </Typography.Paragraph>
    </PageHeader>
    <CustomFieldsTable />
  </Layout>
);
export default CustomFields;
