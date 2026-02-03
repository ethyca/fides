import { Result } from "fidesui";
import { NextPage } from "next";

import { CreateChatProviderConfiguration } from "~/features/chat-provider/CreateChatProviderConfiguration";
import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";

const ConfigureChatProviderPage: NextPage = () => {
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

  return <CreateChatProviderConfiguration />;
};

export default ConfigureChatProviderPage;
