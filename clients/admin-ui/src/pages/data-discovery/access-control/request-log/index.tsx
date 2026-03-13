import { Icons } from "fidesui";
import type { NextPage } from "next";

import AccessControlTabs from "~/features/access-control/AccessControlTabs";
import RequestLogTab from "~/features/access-control/RequestLogTab";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const AccessControlRequestLogPage: NextPage = () => {
  return (
    <Layout title="Access control">
      <PageHeader
        heading="Access control"
        isSticky
        rightContent={<Icons.Settings size={20} />}
      />
      <AccessControlTabs />
      <RequestLogTab />
    </Layout>
  );
};

export default AccessControlRequestLogPage;
