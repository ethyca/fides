import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";
import PreApprovalWebhooksPage from "~/features/privacy-requests/pre-approval-webhooks/PreApprovalWebhooksPage";

const PreApprovalWebhooksSettingsPage: NextPage = () => (
  <>
    <SidePanel>
      <SidePanel.Identity title="Pre-approval webhooks" />
    </SidePanel>
    <Layout title="Pre-approval webhooks">
      <PreApprovalWebhooksPage />
    </Layout>
  </>
);

export default PreApprovalWebhooksSettingsPage;
