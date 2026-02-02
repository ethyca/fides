import { ChakraHeading as Heading } from "fidesui";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/BackButton";
import { CHAT_PROVIDERS_ROUTE } from "~/features/common/nav/routes";

import ChatProviderConfiguration from "./ChatProviderConfiguration";

export const CreateChatProviderConfiguration = () => {
  return (
    <Layout title="Create Chat Provider Configuration">
      <BackButton backPath={CHAT_PROVIDERS_ROUTE} />

      <Heading fontSize="2xl" fontWeight="semibold" mb={6}>
        Configure your chat provider
      </Heading>
      <ChatProviderConfiguration />
    </Layout>
  );
};

export default CreateChatProviderConfiguration;
