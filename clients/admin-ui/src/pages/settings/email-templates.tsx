import { Box, Spinner, Text } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import EmailTemplatesForm from "~/features/messaging-templates/EmailTemplatesForm";
import { useGetMessagingTemplatesQuery } from "~/features/messaging-templates/messaging-templates.slice";

const EmailTemplates: NextPage = () => {
  const { data: messagingTemplates, isLoading } =
    useGetMessagingTemplatesQuery();

  if (isLoading) {
    return (
      <Layout title="Email templates">
        <Spinner />
      </Layout>
    );
  }

  return (
    <Layout title="Email templates">
      <Box data-testid="email-templates">
        <PageHeader heading="Email Templates" />
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
  );
};

export default EmailTemplates;
