import { NextPage } from "next";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import Restrict from "~/features/common/Restrict";
import { SidePanel } from "~/features/common/SidePanel";
import { useMessagingConfigurationsTable } from "~/features/messaging/hooks/useMessagingConfigurationsTable";
import { MessagingConfigurations } from "~/features/messaging/MessagingConfigurations";
import { ScopeRegistryEnum } from "~/types/api";

const ProvidersPage: NextPage = () => {
  const { error } = useMessagingConfigurationsTable();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching your messaging configurations"
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Notifications" />
      </SidePanel>
      <Layout title="Notifications">
        <Restrict scopes={[ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE]}>
          <NotificationTabs />
          <MessagingConfigurations />
        </Restrict>
      </Layout>
    </>
  );
};

export default ProvidersPage;
