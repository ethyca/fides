import { Button, Space, Text } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import PoliciesContainer from "~/features/access-policies/PoliciesContainer";
import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_NEW_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const AccessPoliciesPage: NextPage = () => {
  return (
    <Layout title="Access policies">
      <PageHeader
        heading="Access policies"
        rightContent={
          <Space>
            <NextLink href={ACCESS_POLICIES_NEW_ROUTE} passHref>
              <Button type="primary">New policy</Button>
            </NextLink>
          </Space>
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
    </Layout>
  );
};

export default AccessPoliciesPage;
