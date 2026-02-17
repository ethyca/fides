import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import PreApprovalWebhooksPage from "~/features/privacy-requests/pre-approval-webhooks/PreApprovalWebhooksPage";

const PreApprovalWebhooksSettingsPage: NextPage = () => (
  <Layout title="Pre-approval webhooks">
    <PageHeader heading="Pre-approval webhooks" />
    <PreApprovalWebhooksPage />
  </Layout>
);

export default PreApprovalWebhooksSettingsPage;
