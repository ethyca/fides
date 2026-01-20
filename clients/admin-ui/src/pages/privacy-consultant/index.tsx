import { Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const PrivacyConsultantPage: NextPage = () => (
  <Layout title="Privacy Consultant">
    <PageHeader heading="Privacy Consultant" />
    <Typography.Title level={2}>
      Privacy Consultant - Test Page
    </Typography.Title>
  </Layout>
);

export default PrivacyConsultantPage;
