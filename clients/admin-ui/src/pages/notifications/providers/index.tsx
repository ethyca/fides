import { NextPage } from "next";

import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import { MessagingConfigurations } from "~/features/messaging/MessagingConfigurations";
import { ScopeRegistryEnum } from "~/types/api";

const ProvidersPage: NextPage = () => (
  <Layout title="Notifications">
    <Restrict scopes={[ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE]}>
      <PageHeader heading="Notifications" />
      <NotificationTabs />
      <MessagingConfigurations />
    </Restrict>
  </Layout>
);

export default ProvidersPage;
