import { Box } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import NotificationTabs from "~/features/common/NotificationTabs";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import DigestConfigList from "~/features/digests/components/DigestConfigList";
import { ScopeRegistryEnum } from "~/types/api";

const DigestsPage: NextPage = () => {
  return (
    <Layout title="Notifications">
      <Restrict scopes={[ScopeRegistryEnum.DIGEST_CONFIG_READ]}>
        <Box data-testid="digests-management">
          <PageHeader heading="Notifications" />
          <NotificationTabs />
          <Box maxWidth="1200px">
            <DigestConfigList />
          </Box>
        </Box>
      </Restrict>
    </Layout>
  );
};

export default DigestsPage;
