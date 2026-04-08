import { Text } from "fidesui";
import type { NextPage } from "next";

import OnboardingForm from "~/features/access-policies/OnboardingForm";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const AccessPoliciesOnboardingPage: NextPage = () => {
  return (
    <Layout title="Access policies">
      <PageHeader heading="Access policies" isSticky>
        <div className="max-w-3xl">
          <Text type="secondary">
            Access policies define when data processing is permitted or denied.
            Policies are evaluated in priority order and can be grouped into
            controls for organization and reporting.
          </Text>
        </div>
      </PageHeader>
      <OnboardingForm />
    </Layout>
  );
};

export default AccessPoliciesOnboardingPage;
