import { Empty, Flex, List, Skeleton, Tag, Typography } from "fidesui";
import type { NextPage } from "next";
import { useMemo, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import SearchInput from "~/features/common/SearchInput";
import { useGetPoliciesQuery } from "~/features/policy/policy.slice";
import { ActionType, PolicyResponse, RuleResponse } from "~/types/api";

const { Paragraph, Text } = Typography;

const PoliciesPage: NextPage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  const { data: policiesData, isLoading } = useGetPoliciesQuery();

  // Extract unique action types from rules for each policy
  const getActionTypes = (rules?: RuleResponse[] | null): ActionType[] => {
    if (!rules || rules.length === 0) {
      return [];
    }
    const actionTypes = rules.map((rule) => rule.action_type);
    return [...new Set(actionTypes)];
  };

  const allPolicies = useMemo(() => policiesData?.items ?? [], [policiesData]);

  // Filter policies based on search query
  const filteredPolicies = useMemo(() => {
    if (!searchQuery.trim()) {
      return allPolicies;
    }
    const query = searchQuery.toLowerCase();
    return allPolicies.filter(
      (policy) =>
        policy.name.toLowerCase().includes(query) ||
        policy.key?.toLowerCase().includes(query),
    );
  }, [allPolicies, searchQuery]);

  return (
    <FixedLayout title="Policies">
      <PageHeader
        heading="DSR policies"
        breadcrumbItems={[{ title: "All policies" }]}
      />

      <div className="mb-6">
        <Paragraph type="secondary">
          Data Subject Request (DSR) policies define how privacy requests are
          processed. Each policy contains rules that specify actions to take on
          data categories, such as access, erasure, or consent operations.
        </Paragraph>
        <Paragraph type="secondary">
          Policies can also include conditions that determine when the policy
          applies based on request attributes like geography, request type, or
          custom fields.
        </Paragraph>

        <SearchInput
          placeholder="Search policies by name or key..."
          onChange={setSearchQuery}
          value={searchQuery}
          className="max-w-md"
        />
      </div>

      {!isLoading && filteredPolicies.length === 0 && (
        <Empty
          description={
            searchQuery
              ? "No policies match your search"
              : "No policies configured"
          }
          className="py-8"
        />
      )}
      {!isLoading && filteredPolicies.length > 0 && (
        <List
          dataSource={filteredPolicies}
          data-testid="policies-list"
          renderItem={(policy: PolicyResponse) => {
            const actionTypes = getActionTypes(policy.rules);

            return (
              <List.Item key={policy.key ?? policy.name}>
                <List.Item.Meta
                  title={
                    <Flex align="center" gap={8}>
                      <Text strong>{policy.name}</Text>
                      {actionTypes.map((actionType) => (
                        <Tag key={actionType} className="capitalize">
                          {actionType}
                        </Tag>
                      ))}
                    </Flex>
                  }
                  description={<Text type="secondary">{policy.key}</Text>}
                />
                {policy.execution_timeframe && (
                  <div className="mr-4">
                    <Text type="secondary">
                      Timeframe: {policy.execution_timeframe} days
                    </Text>
                  </div>
                )}
              </List.Item>
            );
          }}
        />
      )}
      {isLoading && (
        <List>
          <List.Item>
            <Skeleton title={false} active />
          </List.Item>
          <List.Item>
            <Skeleton title={false} active />
          </List.Item>
          <List.Item>
            <Skeleton title={false} active />
          </List.Item>
        </List>
      )}
    </FixedLayout>
  );
};

export default PoliciesPage;
