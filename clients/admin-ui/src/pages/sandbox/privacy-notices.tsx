import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { SidePanel } from "~/features/common/SidePanel";

import PrivacyNoticeSandboxRealData from "../../features/poc/privacy-notices-sandbox/PrivacyNoticeSandboxRealData";

const PrivacyNoticesSandbox: NextPage = () => {
  return (
    <>
      <SidePanel>
        <SidePanel.Identity title="Privacy Notices Sandbox" />
      </SidePanel>
      <Layout title="Privacy Notices Sandbox">
        <PrivacyNoticeSandboxRealData />
      </Layout>
    </>
  );
};

export default PrivacyNoticesSandbox;
