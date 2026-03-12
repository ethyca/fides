import { Button, Space, Text } from "fidesui";
import type { NextPage } from "next";
import NextLink from "next/link";

import OnboardingForm from "~/features/access-policies/OnboardingForm";
import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

const AccessPoliciesOnboardingPage: NextPage = () => {
  return (
    <Layout title="Policy configuration">
      <PageHeader
        heading="Policy configuration"
        isSticky={false}
        rightContent={
          <Space>
            <NextLink href={ACCESS_POLICIES_ROUTE} passHref>
              <Button>View policies</Button>
            </NextLink>
            <NextLink href={ACCESS_POLICIES_ROUTE} passHref>
              <Button type="primary">Generate policies</Button>
            </NextLink>
          </Space>
        }
      >
        <div className="max-w-3xl">
          <Text type="secondary">
            Specify the industry context and specific datasets to prioritize
            during discovery. This ensures our AI focusing on the most relevant
            signals for your environment.
          </Text>
        </div>
      </PageHeader>
      <div className="mt-6">
        <OnboardingForm />
      </div>
    </Layout>
  );
};

export default AccessPoliciesOnboardingPage;
