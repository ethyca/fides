import { Box } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import DigestConfigList from "~/features/digests/components/DigestConfigList";
import { ScopeRegistryEnum } from "~/types/api";

const DigestsPage: NextPage = () => {
  return (
    <Layout title="Digests">
      <Restrict scopes={[ScopeRegistryEnum.DIGEST_CONFIG_READ]}>
        <Box data-testid="digests-management">
          <PageHeader heading="Digest Configurations" />
          <Box maxWidth="1200px">
            <DigestConfigList />
          </Box>
        </Box>
      </Restrict>
    </Layout>
  );
};

export default DigestsPage;
