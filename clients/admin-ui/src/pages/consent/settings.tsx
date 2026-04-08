import type { NextPage } from "next";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import ConsentSettingsContent from "~/features/consent-settings/ConsentSettingsContent";
import DomainsContent from "~/features/consent-settings/DomainsContent";
import ErrorPage from "~/features/common/errors/ErrorPage";
import PropertiesTable from "~/features/properties/PropertiesTable";
import usePropertiesTable from "~/features/properties/usePropertiesTable";

const VIEWS = {
  PROPERTIES: "properties",
  DOMAINS: "domains",
  TCF_CONSENT: "tcf-consent",
} as const;

type ViewKey = (typeof VIEWS)[keyof typeof VIEWS];

const PropertiesView: React.FC = () => {
  const { error } = usePropertiesTable();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching properties"
      />
    );
  }

  return <PropertiesTable />;
};

const ConsentSettingsHub: NextPage = () => {
  const [activeView, setActiveView] = useState<ViewKey>(VIEWS.PROPERTIES);

  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Consent Settings" />
        <SidePanel.Navigation
          items={[
            { key: VIEWS.PROPERTIES, label: "Properties" },
            { key: VIEWS.DOMAINS, label: "Domains" },
            { key: VIEWS.TCF_CONSENT, label: "TCF & Consent" },
          ]}
          activeKey={activeView}
          onSelect={(key) => setActiveView(key as ViewKey)}
        />
      </SidePanel>
      <Layout title="Consent Settings">
        {activeView === VIEWS.PROPERTIES && <PropertiesView />}
        {activeView === VIEWS.DOMAINS && <DomainsContent />}
        {activeView === VIEWS.TCF_CONSENT && <ConsentSettingsContent />}
      </Layout>
    </>
  );
};

export default ConsentSettingsHub;
