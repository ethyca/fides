import { NextPage } from "next";

import { ChatConfigurations } from "~/features/chat-provider/ChatConfigurations";
import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

const ChatProvidersPage: NextPage = () => {
  return (
    <Layout title="Notifications">
      <Restrict scopes={[ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE]}>
        <PageHeader heading="Notifications" />
        <NotificationTabs />
        <ChatConfigurations />
      </Restrict>
    </Layout>
  );
};

export default ChatProvidersPage;
