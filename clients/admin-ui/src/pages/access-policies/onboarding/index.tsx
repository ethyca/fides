import { Text } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import OnboardingForm from "~/features/access-policies/OnboardingForm";
import Layout from "~/features/common/Layout";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

// This page is temporary - just serves as a convenient route for demoing.
// Should be removed once no longer needed.
const AccessPoliciesOnboardingPage: NextPage = () => {
  const router = useRouter();

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
      <OnboardingForm onComplete={() => router.push(ACCESS_POLICIES_ROUTE)} />
    </Layout>
  );
};

export default AccessPoliciesOnboardingPage;
