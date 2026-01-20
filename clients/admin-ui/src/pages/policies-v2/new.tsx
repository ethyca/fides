import { ChakraText as Text } from "fidesui";
import { useRouter } from "next/router";
import React, { useMemo } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import PolicyV2Form from "~/features/policy-v2/PolicyV2Form";
import { PolicyV2 } from "~/features/policy-v2/types";

const NewPolicyV2Page = () => {
  const router = useRouter();

  // Parse prefilled policy from query parameter (from AI chat)
  const prefillPolicy = useMemo((): PolicyV2 | undefined => {
    if (router.query.prefill && typeof router.query.prefill === "string") {
      try {
        const parsed = JSON.parse(router.query.prefill);
        // Add a placeholder id if not present (required for PolicyV2 type)
        return {
          id: "",
          ...parsed,
        } as PolicyV2;
      } catch {
        return undefined;
      }
    }
    return undefined;
  }, [router.query.prefill]);

  return (
    <FixedLayout title="Create Policy">
      <PageHeader heading="Create New Policy">
        <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
          {prefillPolicy
            ? "Review the AI-generated policy below and make any adjustments before saving."
            : "Create a new runtime policy with rules that define how data processing decisions are made based on privacy declarations and consent status."}
        </Text>
      </PageHeader>
      <PolicyV2Form policy={prefillPolicy} />
    </FixedLayout>
  );
};

export default NewPolicyV2Page;
