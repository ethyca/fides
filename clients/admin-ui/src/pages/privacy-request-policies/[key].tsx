import { Flex, PageSpinner, Tabs, useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import PolicyConditionsTab from "~/features/policies/conditions/ConditionsTab";
import {
  useDeletePolicyMutation,
  useGetPolicyQuery,
} from "~/features/policies/policy.slice";
import { PolicyBox } from "~/features/policies/PolicyBox";
import { PolicyFormModal } from "~/features/policies/PolicyFormModal";
import { RulesTab } from "~/features/policies/rules/RulesTab";

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

  const [deletePolicy, { isLoading: isDeleting }] = useDeletePolicyMutation();

  const handleDelete = async () => {
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
  };

  const tabs = useMemo(
    () => [
      {
        key: TAB_KEYS.RULES,
        label: `Rules (${policy?.rules?.length ?? 0})`,
        children: <RulesTab rules={policy?.rules ?? []} />,
      },
      {
        key: TAB_KEYS.CONDITIONS,
        label: "Conditions",
        children: <PolicyConditionsTab />,
      },
    ],
    [policy?.rules],
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
    <Layout title="Policies">
      <PageHeader
        heading="DSR policies"
        breadcrumbItems={[
          {
            title: "All policies",
            href: POLICIES_ROUTE,
          },
          {
            title: policy?.name ?? policy?.key ?? "Policy",
          },
        ]}
      />

      {isLoading && <PageSpinner />}

      {policy && (
        <Flex vertical gap="large">
          <PolicyBox
            policy={policy}
            onEdit={() => setIsEditModalOpen(true)}
            onDelete={handleDelete}
            isDeleting={isDeleting}
          />
          <Tabs items={tabs} activeKey={activeTab} onChange={onTabChange} />
        </Flex>
      )}

      <PolicyFormModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        policyKey={policyKey}
      />
    </Layout>
  );
};

export default PolicyDetailPage;
