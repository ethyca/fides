import { Typography } from "fidesui";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/BackButton";
import { CHAT_PROVIDERS_ROUTE } from "~/features/common/nav/routes";

import ChatProviderConfiguration from "./ChatProviderConfiguration";

const { Title } = Typography;

export const CreateChatProviderConfiguration = () => {
  return (
    <Layout title="Create chat provider configuration">
      <BackButton backPath={CHAT_PROVIDERS_ROUTE} />

      <Title level={2} style={{ marginBottom: 24 }}>
        Configure your chat provider
      </Title>
      <ChatProviderConfiguration />
    </Layout>
  );
};

export default CreateChatProviderConfiguration;
