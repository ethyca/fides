import { Typography } from "fidesui";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/BackButton";
import { CHAT_PROVIDERS_ROUTE } from "~/features/common/nav/routes";

import ChatConfiguration from "./ChatConfiguration";

const { Title } = Typography;

export const CreateChatConfiguration = () => {
  return (
    <Layout title="Create chat configuration">
      <BackButton backPath={CHAT_PROVIDERS_ROUTE} />

      <Title level={2} style={{ marginBottom: 24 }}>
        Configure your chat provider
      </Title>
      <ChatConfiguration />
    </Layout>
  );
};

export default CreateChatConfiguration;
