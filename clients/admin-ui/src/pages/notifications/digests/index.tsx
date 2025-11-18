import { AntFlex as Flex } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import PageHeader from "~/features/common/PageHeader";
import DigestConfigList from "~/features/digests/components/DigestConfigList";

const DigestsPage: NextPage = () => {
  return (
    <Layout title="Notifications">
      <Flex vertical data-testid="digests-management">
        <PageHeader heading="Notifications" />
        <NotificationTabs />
        <DigestConfigList />
      </Flex>
    </Layout>
  );
};

export default DigestsPage;
