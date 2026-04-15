import { Button, Flex, Icons, Text } from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import { useGetAccessPoliciesQuery } from "~/features/access-policies/access-policies.slice";
import PoliciesContainer from "~/features/access-policies/PoliciesContainer";
import PolicySettingsModal from "~/features/access-policies/PolicySettingsModal";
import { useFlags } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { RouterLink } from "~/features/common/nav/RouterLink";
import {
  ACCESS_POLICIES_NEW_ROUTE,
  CONTROLS_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const AccessPoliciesPage: NextPage = () => {
  const { flags } = useFlags();
  const { data, isLoading } = useGetAccessPoliciesQuery({});
  const hasPolicies = !isLoading && (data?.items?.length ?? 0) > 0;
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <Layout title="Access policies">
      <PageHeader
        heading="Access policies"
        rightContent={
          hasPolicies ? (
            <Flex gap={8}>
              <NextLink href={CONTROLS_ROUTE} passHref>
                <Button>Manage controls</Button>
              </NextLink>
              {flags.alphaPrivacyDocUpload && (
                <Button
                  aria-label="Policy settings"
                  icon={<Icons.Settings />}
                  onClick={() => setSettingsOpen(true)}
                />
              )}
              <RouterLink href={ACCESS_POLICIES_NEW_ROUTE}>
                <Button type="primary">New policy</Button>
              </RouterLink>
            </Flex>
          ) : undefined
        }
        isSticky
      >
        <div className="max-w-3xl">
          <Text type="secondary">
            Access policies define when data processing is permitted or denied.
            Policies are evaluated in priority order and can be grouped into
            controls for organization and reporting.
          </Text>
        </div>
      </PageHeader>
      <PoliciesContainer />
      {flags.alphaPrivacyDocUpload && (
        <PolicySettingsModal
          open={settingsOpen}
          onClose={() => setSettingsOpen(false)}
        />
      )}
    </Layout>
  );
};

export default AccessPoliciesPage;
