import type { NextPage } from "next";

import { AccessControlTabs } from "~/features/access-control/AccessControlTabs";
import { RequestLogPage } from "~/features/access-control/request-log/RequestLogPage";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const AccessControlRequestLogPage: NextPage = () => {
  return (
    <Layout title="Access control">
      <PageHeader heading="Access control" isSticky />
      <div className="px-6">
        <AccessControlTabs />
        <RequestLogPage />
      </div>
    </Layout>
  );
};

export default AccessControlRequestLogPage;
