import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import PrivacyConsultantChat from "~/features/privacy-consultant/PrivacyConsultantChat";

const PrivacyConsultantPage: NextPage = () => (
  <Layout title="Privacy Consultant">
    <PageHeader heading="Privacy consultant" />
    <PrivacyConsultantChat />
  </Layout>
);

export default PrivacyConsultantPage;
