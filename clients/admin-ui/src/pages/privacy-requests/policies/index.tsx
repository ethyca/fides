import { Empty, Flex, List, Skeleton, Tag, Typography } from "fidesui";
import { uniqBy } from "lodash";
import type { NextPage } from "next";
import { useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import { POLICY_DETAIL_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import SearchInput from "~/features/common/SearchInput";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useGetPoliciesQuery } from "~/features/policy/policy.slice";
import { PolicyResponse } from "~/types/api";

const { Paragraph, Text } = Typography;

const PoliciesPage: NextPage = () => {
  const [searchQuery, setSearchQuery] = useState("");

  const { data: policiesData, isLoading } = useGetPoliciesQuery();

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
    <Layout title="Policies">
      <PageHeader
        heading="DSR policies"
        breadcrumbItems={[{ title: "All policies" }]}
      >
        <Paragraph className="max-w-screen-md">
          DSR policies define how privacy requests are processed. Each policy
          contains rules that specify actions like access or erasure, and
          conditions that determine when the policy applies.
        </Paragraph>
        <SearchInput
          placeholder="Search policies by name or key..."
          onChange={setSearchQuery}
          value={searchQuery}
          className="max-w-md"
        />
      </PageHeader>

      <Flex vertical gap="large">
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
              const uniqueRules = uniqBy(policy.rules ?? [], "action_type");

              return (
                <List.Item key={policy.key ?? policy.name}>
                  <List.Item.Meta
                    title={
                      <Flex align="center" gap={8}>
                        <LinkCell
                          href={{
                            pathname: POLICY_DETAIL_ROUTE,
                            query: { key: policy.key },
                          }}
                        >
                          {policy.name}
                        </LinkCell>
                        {uniqueRules.map((rule) => (
                          <Tag key={rule.action_type} className="capitalize">
                            {rule.action_type}
                          </Tag>
                        ))}
                      </Flex>
                    }
                    description={<Text type="secondary">{policy.key}</Text>}
                  />
                  {policy.execution_timeframe && (
                    <Text type="secondary">
                      Timeframe: {policy.execution_timeframe} days
                    </Text>
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
      </Flex>
    </Layout>
  );
};

export default PoliciesPage;
