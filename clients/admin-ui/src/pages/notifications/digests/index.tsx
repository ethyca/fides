import { Box } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import PageHeader from "~/features/common/PageHeader";
import DigestConfigList from "~/features/digests/components/DigestConfigList";

const DigestsPage: NextPage = () => {
  return (
    <Layout title="Notifications">
      <Box data-testid="digests-management">
        <PageHeader heading="Notifications" />
        <NotificationTabs />
        <Box maxWidth="1200px">
          <DigestConfigList />
        </Box>
      </Box>
    </Layout>
  );
};

export default DigestsPage;
