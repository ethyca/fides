import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import PrivacyRequestRedactionPatternsPage from "~/features/settings/PrivacyRequestRedactionPatternsPage";

const PrivacyRequestRedactionPatternsSettingsPage: NextPage = () => (
  <Layout title="Privacy request redaction patterns">
    <PageHeader heading="Privacy request redaction patterns" />
    <PrivacyRequestRedactionPatternsPage />
  </Layout>
);

export default PrivacyRequestRedactionPatternsSettingsPage;
