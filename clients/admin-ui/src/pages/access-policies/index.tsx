import { Button, Flex, Text } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useState } from "react";

import { useGetAccessPoliciesQuery } from "~/features/access-policies/access-policies.slice";
import ManageControlsModal from "~/features/access-policies/ManageControlsModal";
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
  const [controlsModalOpen, setControlsModalOpen] = useState(false);

  return (
    <Layout title="Access policies">
      <PageHeader
        heading="Access policies"
        rightContent={
          hasPolicies ? (
            <Flex gap={8}>
              <Button onClick={() => setControlsModalOpen(true)}>
                Manage controls
              </Button>
              {flags.alphaPrivacyDocUpload && (
                <Button onClick={() => setSettingsOpen(true)}>
                  Policy settings
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
      <ManageControlsModal
        open={controlsModalOpen}
        onClose={() => setControlsModalOpen(false)}
      />
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
