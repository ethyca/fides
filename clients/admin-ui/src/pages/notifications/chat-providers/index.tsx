import { NextPage } from "next";

import { ChatConfigurations } from "~/features/chat-provider/ChatConfigurations";
import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import Restrict from "~/features/common/Restrict";
import { SidePanel } from "~/features/common/SidePanel";
import { ScopeRegistryEnum } from "~/types/api";

const ChatProvidersPage: NextPage = () => {
  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Notifications" />
      </SidePanel>
      <Layout title="Notifications">
        <Restrict scopes={[ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE]}>
          <NotificationTabs />
          <ChatConfigurations />
        </Restrict>
      </Layout>
    </>
  );
};

export default ChatProvidersPage;
