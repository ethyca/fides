import { Typography } from "fidesui";
import type { NextPage } from "next";

import SlackIntegrationCard from "~/features/chat-provider/SlackIntegrationCard";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const { Paragraph } = Typography;

const NotificationIntegrationsPage: NextPage = () => {
  return (
    <Layout title="Notification integrations">
      <PageHeader heading="Integrations" />
      <Paragraph className="mb-6">
        Connect third-party services to receive AI-powered privacy insights and
        alerts.
      </Paragraph>
      <SlackIntegrationCard />
    </Layout>
  );
};

export default NotificationIntegrationsPage;
