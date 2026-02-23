import { ChakraSpinner as Spinner, Tabs } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo } from "react";

import ErrorPage from "~/features/common/errors/ErrorPage";
import FixedLayout from "~/features/common/FixedLayout";
import { POLICIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import useURLHashedTabs from "~/features/common/tabs/useURLHashedTabs";
import PolicyConditionsTab from "~/features/policies/conditions/PolicyConditionsTab";
import PolicyBox from "~/features/policies/PolicyBox";
import RulesTab from "~/features/policies/rules/RulesTab";
import {
  useDeletePolicyMutation,
  useGetPolicyQuery,
  useGetPolicyRulesQuery,
} from "~/features/policy/policy.slice";

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

  const { data: rulesData } = useGetPolicyRulesQuery(policyKey, {
    skip: !policyKey,
  });

  const [deletePolicy, { isLoading: isDeleting }] = useDeletePolicyMutation();

  const handleDelete = async () => {
    if (!policyKey) {
      return;
    }
    await deletePolicy(policyKey);
    router.push(POLICIES_ROUTE);
  };

  const tabs = useMemo(
    () => [
      {
        key: TAB_KEYS.RULES,
        label: `Rules (${rulesData?.items?.length ?? 0})`,
        children: <RulesTab policyKey={policyKey} />,
      },
      {
        key: TAB_KEYS.CONDITIONS,
        label: "Conditions",
        children: <PolicyConditionsTab policyKey={policyKey} />,
      },
    ],
    [policyKey, rulesData?.items?.length],
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
    <FixedLayout title="Policies">
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

      {isLoading ? (
        <div className="flex justify-center py-8">
          <Spinner />
        </div>
      ) : (
        policy && (
          <>
            <PolicyBox
              policy={policy}
              onDelete={handleDelete}
              isDeleting={isDeleting}
            />

            <Tabs items={tabs} activeKey={activeTab} onChange={onTabChange} />
          </>
        )
      )}
    </FixedLayout>
  );
};

export default PolicyDetailPage;
