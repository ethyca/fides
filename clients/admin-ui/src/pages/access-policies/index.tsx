import { Button, Flex, Text } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useState } from "react";

import { useGetAccessPoliciesQuery } from "~/features/access-policies/access-policies.slice";
import PoliciesContainer from "~/features/access-policies/PoliciesContainer";
import PolicySettingsModal from "~/features/access-policies/PolicySettingsModal";
import { useFlags } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_NEW_ROUTE } from "~/features/common/nav/routes";
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
              {flags.alphaPrivacyDocUpload && (
                <Button onClick={() => setSettingsOpen(true)}>
                  Policy config
                </Button>
              )}
              <NextLink href={ACCESS_POLICIES_NEW_ROUTE} passHref>
                <Button type="primary">New policy</Button>
              </NextLink>
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
