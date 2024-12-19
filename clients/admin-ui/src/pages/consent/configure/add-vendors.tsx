import { AntTypography as Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { CONFIGURE_CONSENT_ROUTE } from "~/features/common/nav/v2/routes";
import PageHeader from "~/features/common/PageHeader";
import { AddMultipleSystems } from "~/features/system/add-multiple-systems/AddMultipleSystems";

const { Text } = Typography;

const AddMultipleVendorsPage: NextPage = () => (
  <Layout title="Choose vendors">
    <PageHeader
      heading="Vendors"
      breadcrumbItems={[
        { title: "All vendors", href: CONFIGURE_CONSENT_ROUTE },
        { title: "Choose vendors" },
      ]}
    >
      <Text className="block w-1/2">
        Select your vendors below and they will be added as systems to your data
        map. Fides Compass will automatically populate the system information so
        that you can quickly configure privacy requests and consent.
      </Text>
    </PageHeader>
    <AddMultipleSystems redirectRoute={CONFIGURE_CONSENT_ROUTE} />
  </Layout>
);

export default AddMultipleVendorsPage;
