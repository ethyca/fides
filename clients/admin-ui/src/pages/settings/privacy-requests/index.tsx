import { Flex } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import PrivacyRequestDuplicateDetectionSettings from "~/features/settings/PrivacyRequestDuplicateDetectionSettings";
import PrivacyRequestRedactionPatternsPage from "~/features/settings/PrivacyRequestRedactionPatternsPage";

const PrivacyRequestRedactionPatternsSettingsPage: NextPage = () => (
  <>
    <SidePanel>
      <SidePanel.Identity title="Privacy request settings" />
    </SidePanel>
    <Layout title="Privacy request settings">
      <Flex vertical gap="large">
        <PrivacyRequestRedactionPatternsPage />
        <PrivacyRequestDuplicateDetectionSettings />
      </Flex>
    </Layout>
  </>
);

export default PrivacyRequestRedactionPatternsSettingsPage;
