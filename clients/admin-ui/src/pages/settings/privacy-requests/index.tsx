import { Flex } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import PrivacyRequestDuplicateDetectionSettings from "~/features/settings/PrivacyRequestDuplicateDetectionSettings";
import PrivacyRequestRedactionPatternsPage from "~/features/settings/PrivacyRequestRedactionPatternsPage";

const PrivacyRequestRedactionPatternsSettingsPage: NextPage = () => (
  <Layout title="Privacy request settings">
    <PageHeader heading="Privacy request settings" />
    <Flex vertical gap="large">
      <PrivacyRequestRedactionPatternsPage />
      <PrivacyRequestDuplicateDetectionSettings />
    </Flex>
  </Layout>
);

export default PrivacyRequestRedactionPatternsSettingsPage;
