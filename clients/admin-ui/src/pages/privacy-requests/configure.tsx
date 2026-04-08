import { Flex } from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import { PRIVACY_REQUESTS_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import DigestConfigList from "~/features/digests/components/DigestConfigList";
import MessagingTemplatesContent from "~/features/messaging-templates/MessagingTemplatesContent";
import { StorageConfigurationContent } from "~/features/privacy-requests/configuration/StorageConfiguration";
import PrivacyRequestDuplicateDetectionSettings from "~/features/settings/PrivacyRequestDuplicateDetectionSettings";
import PrivacyRequestRedactionPatternsPage from "~/features/settings/PrivacyRequestRedactionPatternsPage";

const VIEWS = {
  REDACTION: "redaction",
  DUPLICATE: "duplicate",
  STORAGE: "storage",
  TEMPLATES: "templates",
  DIGESTS: "digests",
} as const;

const ConfigurationHub: NextPage = () => {
  const [activeView, setActiveView] = useState<string>(VIEWS.REDACTION);

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Configuration"
          breadcrumbItems={[
            { title: "Privacy Requests", href: PRIVACY_REQUESTS_ROUTE },
            { title: "Configuration" },
          ]}
        />
        <SidePanel.Navigation
          items={[
            { key: VIEWS.REDACTION, label: "Redaction Patterns" },
            { key: VIEWS.DUPLICATE, label: "Duplicate Detection" },
            { key: VIEWS.STORAGE, label: "Storage" },
            { key: VIEWS.TEMPLATES, label: "Messaging Templates" },
            { key: VIEWS.DIGESTS, label: "Digests" },
          ]}
          activeKey={activeView}
          onSelect={setActiveView}
        />
      </SidePanel>
      <Layout title="Configuration">
        <Flex vertical gap="large">
          {activeView === VIEWS.REDACTION && (
            <PrivacyRequestRedactionPatternsPage />
          )}
          {activeView === VIEWS.DUPLICATE && (
            <PrivacyRequestDuplicateDetectionSettings />
          )}
          {activeView === VIEWS.STORAGE && <StorageConfigurationContent />}
          {activeView === VIEWS.TEMPLATES && <MessagingTemplatesContent />}
          {activeView === VIEWS.DIGESTS && <DigestConfigList />}
        </Flex>
      </Layout>
    </>
  );
};

export default ConfigurationHub;
