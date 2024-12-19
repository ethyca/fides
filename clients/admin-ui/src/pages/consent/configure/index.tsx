import { AntTypography as Typography } from "fidesui";
import React from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { ConsentManagementTable } from "~/features/configure-consent/ConsentManagementTable";

const { Text } = Typography;

const ConfigureConsentPage = () => (
  <Layout title="Vendors">
    <PageHeader heading="Vendors">
      <Text className="block w-1/2">
        Use the table below to manage your vendors. Modify the legal basis for a
        vendor if permitted and view and group your views by applying different
        filters
      </Text>
    </PageHeader>
    <ConsentManagementTable />
  </Layout>
);

export default ConfigureConsentPage;
