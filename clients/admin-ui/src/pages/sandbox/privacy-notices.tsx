import {
  AntLayout as Layout,
  AntTabs as Tabs,
  AntTypography as Typography,
} from "fidesui";
import type { NextPage } from "next";

import PageHeader from "~/features/common/PageHeader";

import PrivacyNoticeSandboxRealData from "../../features/poc/privacy-notices-sandbox/PrivacyNoticeSandboxRealData";
import PrivacyNoticeSandboxSimulated from "../../features/poc/privacy-notices-sandbox/PrivacyNoticeSandboxSimulated";

const { Content } = Layout;

const PrivacyNoticesSandbox: NextPage = () => {
  return (
    <Layout>
      <Content className="overflow-auto px-10 py-6">
        <PageHeader heading="Privacy Notices Sandbox" />

        <Tabs defaultActiveKey="simulated" className="mt-5">
          <Tabs.TabPane tab="Simulated data" key="simulated">
            <PrivacyNoticeSandboxSimulated />
          </Tabs.TabPane>

          <Tabs.TabPane tab="Real data" key="real">
            <PrivacyNoticeSandboxRealData />
          </Tabs.TabPane>
        </Tabs>
      </Content>
    </Layout>
  );
};

export default PrivacyNoticesSandbox;
