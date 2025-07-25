import { Box, Heading } from "fidesui";

import Layout from "~/features/common/Layout";
import BackButton from "~/features/common/nav/BackButton";
import { MESSAGING_PROVIDERS_ROUTE } from "~/features/common/nav/routes";

import MessagingConfiguration from "./MessagingConfiguration";

export const CreateMessagingConfiguration = () => {
  return (
    <Layout title="Create Messaging Configuration">
      <BackButton backPath={MESSAGING_PROVIDERS_ROUTE} />

      <Heading fontSize="2xl" fontWeight="semibold">
        Configure your messaging provider
      </Heading>

      <Box display="flex" flexDirection="column" width="50%">
        <MessagingConfiguration />
      </Box>
    </Layout>
  );
};
