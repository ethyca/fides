import { Button, Space, Text } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import PoliciesGrid from "~/features/access-policies/PoliciesGrid";
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
            <Button>Manage controls</Button>
            <NextLink href={ACCESS_POLICIES_NEW_ROUTE} passHref>
              <Button type="primary">New policy</Button>
            </NextLink>
          </Space>
        }
        isSticky
      >
        <div className="max-w-[75%]">
          <Text type="secondary">
            Purpose Based Access Control (PBAC) policies govern when systems and
            users can access data based on its intended use. Policies are
            organized into controls determined by your business vertical and
            regulatory environment. Select &quot;Manage controls&quot; to add,
            edit, or remove controls.{" "}
            <a
              href="https://docs.ethyca.com/guides/access-policies"
              target="_blank"
              rel="noopener noreferrer"
            >
              Learn more about PBAC
            </a>
          </Text>
        </div>
      </PageHeader>
      <PoliciesGrid />
    </Layout>
  );
};

export default AccessPoliciesPage;
