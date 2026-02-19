import { Flex, PageSpinner, Tabs } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import Layout from "~/features/common/Layout";
import { POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import PolicyConditionsTab from "~/features/policies/conditions/PolicyConditionsTab";
import PolicyBox from "~/features/policies/PolicyBox";
import RulesTab from "~/features/policies/rules/RulesTab";
import { useGetPolicyQuery } from "~/features/policy/policy.slice";

const TAB_KEYS = {
  RULES: "rules",
  CONDITIONS: "conditions",
} as const;

const PolicyDetailPage: NextPage = () => {
  const router = useRouter();
  const policyKey = router.query.key as string;

  const {
    data: policy,
    isLoading,
    error,
  } = useGetPolicyQuery(policyKey, {
    skip: !policyKey,
  });

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
          <PolicyBox policy={policy} />
          <Tabs items={tabs} activeKey={activeTab} onChange={onTabChange} />
        </Flex>
      )}
    </Layout>
  );
};

export default PolicyDetailPage;
