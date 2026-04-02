import { Button, Icons, Space } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";
import { useState } from "react";

import PolicySettingsModal from "~/features/access-policies/PolicySettingsModal";
import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_NEW_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const AccessPoliciesPage: NextPage = () => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <Layout title="Access policies">
      <PageHeader
        heading="Access policies"
        rightContent={
          <Space>
            <Button
              type="text"
              icon={<Icons.Settings size={16} />}
              onClick={() => setIsSettingsOpen(true)}
            >
              Policy config
            </Button>
            <NextLink href={ACCESS_POLICIES_NEW_ROUTE} passHref>
              <Button type="primary">New policy</Button>
            </NextLink>
          </Space>
        }
        isSticky
      />
      <PolicySettingsModal
        open={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />
    </Layout>
  );
};

export default AccessPoliciesPage;
