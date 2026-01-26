import { ChakraText as Text, Icons, Spin, Tabs } from "fidesui";
import { useRouter } from "next/router";
import React from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import PolicyV2Form from "~/features/policy-v2/PolicyV2Form";
import { PolicyFlowBuilder } from "~/features/policy-v2/PolicyFlowBuilder/PolicyFlowBuilder";
import { useGetPolicyV2ByKeyQuery } from "~/features/policy-v2/policy-v2.slice";

enum PolicyTabKeys {
  FORM_EDITOR = "form-editor",
  FLOW_BUILDER = "flow-builder",
}

const EditPolicyV2Page = () => {
  const router = useRouter();
  const { fidesKey } = router.query;

  const { data: policy, isLoading } = useGetPolicyV2ByKeyQuery(
    fidesKey as string,
    {
      skip: !fidesKey,
    },
  );

  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: Object.values(PolicyTabKeys),
    initialTab: PolicyTabKeys.FORM_EDITOR,
  });

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

  const tabItems = [
    {
      label: (
        <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Icons.DocumentBlank size={16} />
          Form Editor
        </span>
      ),
      key: PolicyTabKeys.FORM_EDITOR,
      children: <PolicyV2Form policy={policy} />,
    },
    {
      label: (
        <span style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Icons.Flow size={16} />
          Flow Builder
        </span>
      ),
      key: PolicyTabKeys.FLOW_BUILDER,
      children: (
        <div style={{ height: "calc(100vh - 240px)" }}>
          <PolicyFlowBuilder policy={policy} isLoading={isLoading} />
        </div>
      ),
    },
  ];

  return (
    <FixedLayout title={`Edit Policy: ${policy.name}`}>
      <PageHeader heading={`Edit Policy: ${policy.name}`}>
        <Text fontSize="sm" mb={8} width={{ base: "100%", lg: "50%" }}>
          Edit the policy rules and configuration. Changes will take effect
          immediately for new /evaluate requests.
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

export default EditPolicyV2Page;
