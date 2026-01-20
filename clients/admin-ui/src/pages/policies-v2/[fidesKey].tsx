import { ChakraText as Text, Spin } from "fidesui";
import { useRouter } from "next/router";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import PolicyV2Form from "~/features/policy-v2/PolicyV2Form";
import { useGetPolicyV2ByKeyQuery } from "~/features/policy-v2/policy-v2.slice";

const EditPolicyV2Page = () => {
  const router = useRouter();
  const { fidesKey } = router.query;

  const { data: policy, isLoading } = useGetPolicyV2ByKeyQuery(
    fidesKey as string,
    {
      skip: !fidesKey,
    },
  );

  if (isLoading) {
    return (
      <FixedLayout title="Edit Policy">
        <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
          <Spin size="large" />
        </div>
      </FixedLayout>
    );
  }

  if (!policy) {
    return (
      <FixedLayout title="Policy Not Found">
        <PageHeader heading="Policy Not Found">
          <Text fontSize="sm" mb={8}>
            The policy with key "{fidesKey}" was not found.
          </Text>
        </PageHeader>
      </FixedLayout>
    );
  }

  return (
    <FixedLayout title={`Edit Policy: ${policy.name}`}>
      <PageHeader heading={`Edit Policy: ${policy.name}`}>
        <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
          Edit the policy rules and configuration. Changes will take effect
          immediately for new /evaluate requests.
        </Text>
      </PageHeader>
      <PolicyV2Form policy={policy} />
    </FixedLayout>
  );
};

export default EditPolicyV2Page;
