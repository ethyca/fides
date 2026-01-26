import { ChakraText as Text, Icons, Tabs } from "fidesui";
import { useRouter } from "next/router";
import React, { useCallback, useMemo } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { POLICIES_V2_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { PolicyFlowBuilder } from "~/features/policy-v2/PolicyFlowBuilder/PolicyFlowBuilder";
import PolicyV2Form from "~/features/policy-v2/PolicyV2Form";
import { PolicyV2 } from "~/features/policy-v2/types";

enum PolicyTabKeys {
  FORM_EDITOR = "form-editor",
  FLOW_BUILDER = "flow-builder",
}

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

  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: Object.values(PolicyTabKeys),
    initialTab: PolicyTabKeys.FORM_EDITOR,
  });

  // Navigate to the newly created policy after AI creation
  // Include #flow-builder hash to stay on the Flow Builder tab
  const handlePolicyCreated = useCallback(
    (fidesKey: string) => {
      router.push(`${POLICIES_V2_ROUTE}/${fidesKey}#${PolicyTabKeys.FLOW_BUILDER}`);
    },
    [router]
  );

  const tabItems = [
    {
      label: (
        <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Icons.DocumentBlank size={16} />
          Form Editor
        </span>
      ),
      key: PolicyTabKeys.FORM_EDITOR,
      children: <PolicyV2Form policy={prefillPolicy} />,
    },
    {
      label: (
        <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Icons.Flow size={16} />
          AI Flow Builder
        </span>
      ),
      key: PolicyTabKeys.FLOW_BUILDER,
      children: (
        <div style={{ height: "calc(100vh - 240px)" }}>
          <PolicyFlowBuilder
            policy={null}
            isLoading={false}
            onPolicyCreated={handlePolicyCreated}
          />
        </div>
      ),
    },
  ];

  return (
    <FixedLayout title="Create Policy">
      <PageHeader heading="Create New Policy">
        <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
          {prefillPolicy
            ? "Review the AI-generated policy below and make any adjustments before saving."
            : "Create a new runtime policy using the Form Editor or use AI assistance in the Flow Builder."}
        </Text>
      </PageHeader>
      <Tabs
        activeKey={activeTab}
        onChange={onTabChange}
        items={tabItems}
        className="w-full"
      />
    </FixedLayout>
  );
};

export default NewPolicyV2Page;
