import { Layout } from "fidesui";
import type { NextPage } from "next";

import PageHeader from "~/features/common/PageHeader";

import PrivacyNoticeSandboxRealData from "../../features/poc/privacy-notices-sandbox/PrivacyNoticeSandboxRealData";

const { Content } = Layout;

const PrivacyNoticesSandbox: NextPage = () => {
  return (
    <Layout>
      <Content className="overflow-auto px-10 py-6">
        <PageHeader heading="Privacy Notices Sandbox" />
        <PrivacyNoticeSandboxRealData />
      </Content>
    </Layout>
  );
};

export default PrivacyNoticesSandbox;
