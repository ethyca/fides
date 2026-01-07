import Layout from "common/Layout";
import { AntTypography } from "fidesui";
import type { NextPage } from "next";
import React from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import PageHeader from "~/features/common/PageHeader";
import CustomFieldsTable from "~/features/custom-fields/CustomFieldsTable";
import { useGetAllCustomFieldDefinitionsQuery } from "~/features/plus/plus.slice";

const CUSTOM_FIELDS_COPY =
  "Custom fields provide organizations with the capability to capture metrics that are unique to their specific needs, allowing them to create customized reports. These fields can be added to either systems or elements within a taxonomy, and once added, they become reportable fields that are visible on the data map.";

const CustomFields: NextPage = () => {
  const { error } = useGetAllCustomFieldDefinitionsQuery();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching custom fields"
      />
    );
  }
  return (
    <Layout title="Custom fields">
      <PageHeader heading="Custom fields" isSticky={false} className="pb-0">
        <AntTypography.Paragraph className="max-w-screen-md">
          {CUSTOM_FIELDS_COPY}
        </AntTypography.Paragraph>
      </PageHeader>
      <CustomFieldsTable />
    </Layout>
  );
};
export default CustomFields;
