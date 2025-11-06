import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import PrivacyRequestRedactionPatternsPage from "~/features/settings/PrivacyRequestRedactionPatternsPage";

const PrivacyRequestRedactionPatternsSettingsPage: NextPage = () => (
  <Layout title="Privacy request settings">
    <PageHeader heading="Privacy request settings" />
    <PrivacyRequestRedactionPatternsPage />
  </Layout>
);

export default PrivacyRequestRedactionPatternsSettingsPage;
