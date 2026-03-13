import { Button } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const AccessPoliciesOnboardingPage: NextPage = () => {
  return (
    <Layout title="Access policies">
      <PageHeader heading="Get started with access policies" isSticky />
      <div className="p-6">
        <NextLink href={ACCESS_POLICIES_ROUTE} passHref>
          <Button type="primary">Continue</Button>
        </NextLink>
      </div>
    </Layout>
  );
};

export default AccessPoliciesOnboardingPage;
