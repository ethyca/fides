import { Box, Spinner } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { NOTIFICATIONS_DIGESTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import Restrict from "~/features/common/Restrict";
import DigestConfigForm from "~/features/digests/components/DigestConfigForm";
import { useGetDigestConfigByIdQuery } from "~/features/digests/digest-config.slice";
import { ScopeRegistryEnum } from "~/types/api";

const EditDigestPage: NextPage = () => {
  const router = useRouter();
  const { id } = router.query;

  const { data: digestConfig, isLoading } = useGetDigestConfigByIdQuery(
    { config_id: id as string },
    { skip: !id },
  );

  if (isLoading) {
    return (
      <Layout title="Edit Digest">
        <Box className="flex justify-center py-12">
          <Spinner />
        </Box>
      </Layout>
    );
  }

  return (
    <Layout title="Edit Digest">
      <Restrict
        scopes={[
          ScopeRegistryEnum.DIGEST_CONFIG_CREATE,
          ScopeRegistryEnum.DIGEST_CONFIG_UPDATE,
        ]}
      >
        <Box data-testid="edit-digest-config">
          <PageHeader
            heading={digestConfig?.name || "Edit Digest Configuration"}
            breadcrumbItems={[
              { title: "Digests", href: NOTIFICATIONS_DIGESTS_ROUTE },
              { title: digestConfig?.name || "Edit" },
            ]}
          />
          <DigestConfigForm
            initialValues={
              digestConfig
                ? {
                    id: digestConfig.id,
                    name: digestConfig.name,
                    description: digestConfig.description || "",
                    digest_type: digestConfig.digest_type,
                    enabled: digestConfig.enabled,
                    messaging_service_type: digestConfig.messaging_service_type,
                    cron_expression: digestConfig.cron_expression,
                    timezone: digestConfig.timezone,
                  }
                : undefined
            }
            isLoading={isLoading}
          />
        </Box>
      </Restrict>
    </Layout>
  );
};

export default EditDigestPage;
