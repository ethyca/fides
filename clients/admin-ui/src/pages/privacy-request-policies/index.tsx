import {
  Button,
  Empty,
  Flex,
  List,
  Skeleton,
  Tag,
  Tooltip,
  Typography,
  useMessage,
  useModal,
} from "fidesui";
import { uniqBy } from "lodash";
import type { NextPage } from "next";
import { useCallback, useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import { POLICY_DETAIL_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import SearchInput from "~/features/common/SearchInput";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { confirmDeletePolicy } from "~/features/policies/confirmDeletePolicy";
import { DEFAULT_POLICY_TOOLTIP } from "~/features/policies/constants";
import {
  useDeletePolicyMutation,
  useGetDefaultPoliciesQuery,
  useGetPoliciesQuery,
} from "~/features/policies/policy.slice";
import { PolicyFormModal } from "~/features/policies/PolicyFormModal";
import { summarizeConditions } from "~/features/policies/utils/summarizeConditions";
import { PolicyResponse } from "~/types/api";

const { Paragraph, Text } = Typography;

const PoliciesPage: NextPage = () => {
  const message = useMessage();
  const modal = useModal();
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [policyToEdit, setPolicyToEdit] = useState<PolicyResponse | null>(null);

  const { data: policiesData, isLoading } = useGetPoliciesQuery();
  const { data: defaultPoliciesData } = useGetDefaultPoliciesQuery();
  const [deletePolicy] = useDeletePolicyMutation();

  const defaultPolicyKeys = useMemo(() => {
    if (!defaultPoliciesData) {
      return new Set<string>();
    }
    return new Set(Object.values(defaultPoliciesData));
  }, [defaultPoliciesData]);

  const allPolicies = useMemo(() => {
    const items = policiesData?.items ?? [];
    const defaults = items.filter((p) => p.key && defaultPolicyKeys.has(p.key));
    const rest = items
      .filter((p) => !p.key || !defaultPolicyKeys.has(p.key))
      .sort((a, b) => a.name.localeCompare(b.name));
    return [...defaults, ...rest];
  }, [policiesData, defaultPolicyKeys]);

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

  const handleEdit = useCallback((policy: PolicyResponse) => {
    setPolicyToEdit(policy);
  }, []);

  const handleDelete = useCallback(
    (policy: PolicyResponse) => {
      confirmDeletePolicy(modal, policy.name, async () => {
        if (!policy.key) {
          return;
        }
        try {
          await deletePolicy(policy.key).unwrap();
          message.success("Policy deleted successfully");
        } catch {
          message.error("Failed to delete policy");
        }
      });
    },
    [modal, deletePolicy, message],
  );

  return (
    <Layout title="Policies">
      <PageHeader
        heading="DSR policies"
        breadcrumbItems={[{ title: "All policies" }]}
        rightContent={
          <Button
            type="primary"
            onClick={() => setIsCreateModalOpen(true)}
            data-testid="create-policy-btn"
          >
            Create policy
          </Button>
        }
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
              const conditionsSummary = summarizeConditions(policy.conditions);
              const isDefault = !!(
                policy.key && defaultPolicyKeys.has(policy.key)
              );

              return (
                <List.Item
                  key={policy.key ?? policy.name}
                  actions={[
                    <Button
                      key="edit"
                      type="link"
                      onClick={() => handleEdit(policy)}
                      data-testid={`edit-policy-${policy.key}-btn`}
                    >
                      Edit
                    </Button>,
                    <Tooltip
                      key="delete"
                      title={isDefault ? DEFAULT_POLICY_TOOLTIP : undefined}
                    >
                      <Button
                        type="link"
                        disabled={isDefault}
                        onClick={() => handleDelete(policy)}
                        data-testid={`delete-policy-${policy.key}-btn`}
                      >
                        Delete
                      </Button>
                    </Tooltip>,
                  ]}
                >
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
                  <Flex gap="large" align="center">
                    {conditionsSummary && (
                      <Text type="secondary" italic>
                        {conditionsSummary}
                      </Text>
                    )}
                    {policy.execution_timeframe && (
                      <Text type="secondary">
                        {policy.execution_timeframe} days
                      </Text>
                    )}
                  </Flex>
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

      <PolicyFormModal
        isOpen={isCreateModalOpen || !!policyToEdit}
        onClose={() => {
          setIsCreateModalOpen(false);
          setPolicyToEdit(null);
        }}
        policyKey={policyToEdit?.key ?? undefined}
      />
    </Layout>
  );
};

export default PoliciesPage;
