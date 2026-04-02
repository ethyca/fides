import { Button, Text } from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import OnboardingForm from "~/features/access-policies/OnboardingForm";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";

const AccessPoliciesOnboardingPage: NextPage = () => {
  const [canGenerate, setCanGenerate] = useState(false);

  return (
    <Layout title="Policy configuration">
      <PageHeader
        heading="Policy configuration"
        isSticky={false}
        rightContent={
          <Button
            type="primary"
            form="onboarding-form"
            htmlType="submit"
            disabled={!canGenerate}
          >
            Generate policies
          </Button>
        }
      >
        <div className="max-w-3xl">
          <Text type="secondary">
            Specify the industry context and specific datasets to prioritize
            during discovery. These parameters help Fides focus its scanning
            engine on the most relevant signals for your environment and
            auto-generate an initial draft of your access governance policies.
          </Text>
        </div>
      </PageHeader>
      <div className="mt-6">
        <OnboardingForm onCanGenerateChange={setCanGenerate} />
      </div>
    </Layout>
  );
};

export default AccessPoliciesOnboardingPage;
