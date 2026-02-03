import { Result } from "fidesui";
import { NextPage } from "next";

import { ChatProviderConfigurations } from "~/features/chat-provider/ChatProviderConfigurations";
import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

const ChatProvidersPage: NextPage = () => {
  const { flags } = useFeatures();

  if (!flags?.alphaDataProtectionAssessments) {
    return (
      <Layout title="Chat providers">
        <Result
          status="error"
          title="Feature not available"
          subTitle="This feature is currently behind a feature flag and is not enabled."
        />
      </Layout>
    );
  }

  return (
    <Layout title="Notifications">
      <Restrict scopes={[ScopeRegistryEnum.MESSAGING_CREATE_OR_UPDATE]}>
        <PageHeader heading="Notifications" />
        <NotificationTabs />
        <ChatProviderConfigurations />
      </Restrict>
    </Layout>
  );
};

export default ChatProvidersPage;
