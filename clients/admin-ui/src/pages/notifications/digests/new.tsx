import { ChakraBox as Box, Typography } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import { NOTIFICATIONS_DIGESTS_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import Restrict from "~/features/common/Restrict";
import DigestConfigForm from "~/features/digests/components/DigestConfigForm";
import { ScopeRegistryEnum } from "~/types/api";

const { Text } = Typography;

const NewDigestPage: NextPage = () => {
  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title="Create digest"
          breadcrumbItems={[
            { title: "Digests", href: NOTIFICATIONS_DIGESTS_ROUTE },
            { title: "New" },
          ]}
        />
      </SidePanel>
      <Layout title="Create digest">
        <Restrict
          scopes={[
            ScopeRegistryEnum.DIGEST_CONFIG_CREATE,
            ScopeRegistryEnum.DIGEST_CONFIG_UPDATE,
          ]}
        >
          <Box data-testid="new-digest-config">
            <Text className="mb-6 block text-sm">
              Configure a new digest to receive email summaries on a regular
              schedule.
            </Text>
            <DigestConfigForm />
          </Box>
        </Restrict>
      </Layout>
    </>
  );
};

export default NewDigestPage;
