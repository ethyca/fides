import { AntTypography as Typography, Box } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { NOTIFICATIONS_DIGESTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import DigestConfigForm from "~/features/digests/components/DigestConfigForm";
import { ScopeRegistryEnum } from "~/types/api";

const { Text } = Typography;

const NewDigestPage: NextPage = () => {
  return (
    <Layout title="Create Digest">
      <Restrict
        scopes={[
          ScopeRegistryEnum.DIGEST_CONFIG_CREATE,
          ScopeRegistryEnum.DIGEST_CONFIG_UPDATE,
        ]}
      >
        <Box data-testid="new-digest-config">
          <PageHeader
            heading="Create Digest Configuration"
            breadcrumbItems={[
              { title: "Digests", href: NOTIFICATIONS_DIGESTS_ROUTE },
              { title: "New" },
            ]}
          />
          <Text className="mb-6 block text-sm">
            Configure a new digest to receive email summaries on a regular
            schedule.
          </Text>
          <DigestConfigForm />
        </Box>
      </Restrict>
    </Layout>
  );
};

export default NewDigestPage;
