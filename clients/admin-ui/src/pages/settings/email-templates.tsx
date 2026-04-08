import { ChakraBox as Box, ChakraText as Text, Spin } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import EmailTemplatesForm from "~/features/messaging-templates/EmailTemplatesForm";
import { useGetMessagingTemplatesQuery } from "~/features/messaging-templates/messaging-templates.slice";

const EmailTemplates: NextPage = () => {
  const { data: messagingTemplates, isLoading } =
    useGetMessagingTemplatesQuery();

  if (isLoading) {
    return (
      <>
        <SidePanel>
          <SidePanel.Identity title="Email templates" />
        </SidePanel>
        <Layout title="Email templates">
          <Spin />
        </Layout>
      </>
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Email templates" />
      </SidePanel>
      <Layout title="Email templates">
      <Box data-testid="email-templates">
        <Box maxWidth="720px">
          <Text fontSize="sm">
            When privacy requests are submitted, Fides emails the data subject
            to confirm their identity and keep them updated on the status of the
            request. The templates below allow you to configure the subject and
            body of the email to suit your business needs. To change the
            appearance of the email, you may use the editors within your
            messaging provider (e.g. Mailgun, SendGrid, Twilio).
          </Text>
          <Box padding={2}>
            <EmailTemplatesForm emailTemplates={messagingTemplates!} />
          </Box>
        </Box>
      </Box>
      </Layout>
    </>
  );
};

export default EmailTemplates;
