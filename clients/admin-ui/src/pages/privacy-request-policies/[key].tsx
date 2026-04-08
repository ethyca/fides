import { Flex, Spin, useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { POLICIES_ROUTE } from "~/features/common/nav/routes";
import { SidePanel } from "~/features/common/SidePanel";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import { PolicyConditionsTab } from "~/features/policies/conditions/PolicyConditionsTab";
import {
  useDeletePolicyMutation,
  useGetDefaultPoliciesQuery,
  useGetPolicyQuery,
} from "~/features/policies/policy.slice";
import { PolicyBox } from "~/features/policies/PolicyBox";
import { PolicyFormModal } from "~/features/policies/PolicyFormModal";
import { RulesTab } from "~/features/policies/rules/RulesTab";
import { extractLeafConditions } from "~/features/policies/utils/extractLeafConditions";

const TAB_KEYS = {
  RULES: "rules",
  CONDITIONS: "conditions",
} as const;

const PolicyDetailPage: NextPage = () => {
  const router = useRouter();
  const message = useMessage();
  const policyKey = router.query.key as string;
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  const {
    data: policy,
    isLoading,
    error,
  } = useGetPolicyQuery(policyKey, {
    skip: !policyKey,
  });

  const { data: defaultPoliciesData } = useGetDefaultPoliciesQuery();
  const [deletePolicy, { isLoading: isDeleting }] = useDeletePolicyMutation();

  const isDefault = useMemo(() => {
    if (!defaultPoliciesData || !policyKey) {
      return false;
    }
    return Object.values(defaultPoliciesData).includes(policyKey);
  }, [defaultPoliciesData, policyKey]);

  const handleDelete = useCallback(async () => {
    if (!policyKey) {
      return;
    }
    try {
      await deletePolicy(policyKey).unwrap();
      message.success("Policy deleted successfully");
      router.push(POLICIES_ROUTE);
    } catch {
      message.error("Failed to delete policy");
    }
  }, [policyKey, deletePolicy, message, router]);

  const tabs = useMemo(
    () => [
      {
        key: TAB_KEYS.RULES,
        label: `Rules (${policy?.rules?.length ?? 0})`,
        children: <RulesTab rules={policy?.rules ?? []} />,
      },
      {
        key: TAB_KEYS.CONDITIONS,
        label: `Conditions (${extractLeafConditions(policy?.conditions).length})`,
        children: (
          <PolicyConditionsTab
            conditions={policy?.conditions}
            policyKey={policyKey}
          />
        ),
      },
    ],
    [policy?.rules, policy?.conditions, policyKey],
  );

  const { activeTab, onTabChange } = useURLHashedTabs({
    tabKeys: Object.values(TAB_KEYS),
  });

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage={`A problem occurred while fetching the policy ${policyKey}`}
        actions={[
          {
            label: "Return to policies",
            onClick: () => router.push(POLICIES_ROUTE),
          },
        ]}
      />
    );
  }

  return (
    <>
      <SidePanel>
        <SidePanel.Identity
          title={policy?.name ?? policyKey ?? "Policy"}
          breadcrumbItems={[
            { title: "All policies", href: POLICIES_ROUTE },
            { title: policy?.name ?? policy?.key ?? "Policy" },
          ]}
        />
        <SidePanel.Navigation
          items={tabs.map((t) => ({ key: t.key, label: t.label }))}
          activeKey={activeTab}
          onSelect={onTabChange}
        />
      </SidePanel>
      <Layout title="Policies">
        {isLoading && <Spin />}
        {policy && (
          <Flex vertical gap="large">
            <PolicyBox
              policy={policy}
              isDefault={isDefault}
              onEdit={() => setIsEditModalOpen(true)}
              onDelete={handleDelete}
              isDeleting={isDeleting}
            />
            {tabs.find((t) => t.key === activeTab)?.children}
          </Flex>
        )}
        <PolicyFormModal
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          policyKey={policyKey}
        />
      </Layout>
    </>
  );
};

export default PolicyDetailPage;
