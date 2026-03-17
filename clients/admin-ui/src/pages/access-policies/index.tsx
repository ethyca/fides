import { Button, Space } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import {
  ACCESS_POLICIES_NEW_ROUTE,
  ACCESS_POLICIES_ONBOARDING_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const AccessPoliciesPage: NextPage = () => {
  return (
    <Layout title="Access policies">
      <PageHeader
        heading="Access policies"
        rightContent={
          <Space>
            <NextLink href={ACCESS_POLICIES_ONBOARDING_ROUTE} passHref>
              <Button>Onboarding</Button>
            </NextLink>
            <NextLink href={ACCESS_POLICIES_NEW_ROUTE} passHref>
              <Button type="primary">New policy</Button>
            </NextLink>
          </Space>
        }
        isSticky
      />
    </Layout>
  );
};

export default AccessPoliciesPage;
