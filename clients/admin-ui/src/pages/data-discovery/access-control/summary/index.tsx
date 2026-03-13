import { Icons } from "fidesui";
import type { NextPage } from "next";

import AccessControlTabs from "~/features/access-control/AccessControlTabs";
import SummaryTab from "~/features/access-control/SummaryTab";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const AccessControlSummaryPage: NextPage = () => {
  return (
    <Layout title="Access control">
      <PageHeader
        heading="Access control"
        isSticky
        rightContent={<Icons.Settings size={20} />}
      />
      <AccessControlTabs />
      <SummaryTab />
    </Layout>
  );
};

export default AccessControlSummaryPage;
