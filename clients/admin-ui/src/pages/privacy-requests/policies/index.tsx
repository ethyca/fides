import {
  Button,
  Empty,
  Flex,
  List,
  Modal,
  Tag,
  TagProps,
  Typography,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import Link from "next/link";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { POLICY_DETAIL_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import SearchInput from "~/features/common/SearchInput";
import {
  useDeletePolicyMutation,
  useGetPoliciesQuery,
} from "~/features/policy/policy.slice";
import { ActionType, PolicyResponse, RuleResponse } from "~/types/api";

const { Paragraph, Text } = Typography;

// Tag colors from the fidesui palette
const actionTypeColors: Record<ActionType, TagProps["color"]> = {
  [ActionType.ACCESS]: "olive",
  [ActionType.ERASURE]: "marble",
  [ActionType.CONSENT]: "corinth",
  [ActionType.UPDATE]: "sandstone",
};

const PoliciesPage: NextPage = () => {
  const router = useRouter();
  const message = useMessage();
  const [policyToDelete, setPolicyToDelete] = useState<PolicyResponse | null>(
    null,
  );
  const [searchQuery, setSearchQuery] = useState("");

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const { data: policiesData, isLoading } = useGetPoliciesQuery();
  const [deletePolicy] = useDeletePolicyMutation();

  // Combine API policies with mock policies for demo
  const allPolicies = useMemo(() => {
    const apiPolicies = policiesData?.items ?? [];
    // Combine API policies with mock policies for demo
    return [...apiPolicies];
  }, [policiesData]);

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

  // Extract unique action types from rules for each policy
  const getActionTypes = (rules?: RuleResponse[] | null): ActionType[] => {
    if (!rules || rules.length === 0) {
      return [];
    }
    const actionTypes = rules.map((rule) => rule.action_type);
    return [...new Set(actionTypes)];
  };

  const handleEdit = useCallback(
    (policy: PolicyResponse) => {
      router.push({
        pathname: POLICY_DETAIL_ROUTE,
        query: { key: policy.key },
      });
    },
    [router],
  );

  const handleDeleteClick = useCallback((policy: PolicyResponse) => {
    setPolicyToDelete(policy);
    setIsDeleteModalOpen(true);
  }, []);

  const handleConfirmDelete = useCallback(async () => {
    if (!policyToDelete?.key) {
      return;
    }

    try {
      await deletePolicy(policyToDelete.key).unwrap();
      message.success("Policy deleted successfully");
    } catch (err) {
      message.error("Failed to delete policy");
    }

    setPolicyToDelete(null);
    setIsDeleteModalOpen(false);
  }, [policyToDelete, deletePolicy, message]);

  return (
    <FixedLayout title="Policies">
      <PageHeader
        heading="DSR policies"
        breadcrumbItems={[{ title: "All policies" }]}
      />

      <div className="mb-6">
        <Paragraph type="secondary" className="mb-4">
          Data Subject Request (DSR) policies define how privacy requests are
          processed. Each policy contains rules that specify actions to take on
          data categories, such as access, erasure, or consent operations.
          <br />
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

      {isLoading && (
        <div className="py-8 text-center">
          <Text type="secondary">Loading policies...</Text>
        </div>
      )}

      {filteredPolicies.length === 0 ? (
        <Empty
          description={
            searchQuery
              ? "No policies match your search"
              : "No policies configured"
          }
          className="py-8"
        />
      ) : (
        <List
          dataSource={filteredPolicies}
          data-testid="policies-list"
          renderItem={(policy: PolicyResponse) => {
            const actionTypes = getActionTypes(policy.rules);

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
                  <Button
                    key="delete"
                    type="link"
                    onClick={() => handleDeleteClick(policy)}
                    data-testid={`delete-policy-${policy.key}-btn`}
                  >
                    Delete
                  </Button>,
                ]}
              >
                <List.Item.Meta
                  title={
                    <Flex align="center" gap={8}>
                      <Link
                        href={{
                          pathname: POLICY_DETAIL_ROUTE,
                          query: { key: policy.key },
                        }}
                        data-testid={`policy-link-${policy.key}`}
                      >
                        <Text strong>{policy.name}</Text>
                      </Link>
                      {actionTypes.map((actionType) => (
                        <Tag
                          key={actionType}
                          color={actionTypeColors[actionType]}
                          className="capitalize"
                        >
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

      <Modal
        title="Delete policy"
        open={isDeleteModalOpen}
        onCancel={() => {
          setPolicyToDelete(null);
          setIsDeleteModalOpen(false);
        }}
        onOk={handleConfirmDelete}
        okText="Delete"
        okButtonProps={{ danger: true }}
        cancelText="Cancel"
        centered
      >
        <Text type="secondary">
          Are you sure you want to delete the policy &ldquo;
          {policyToDelete?.name}&rdquo;? This action cannot be undone and will
          also delete all associated rules.
        </Text>
      </Modal>
    </FixedLayout>
  );
};

export default PoliciesPage;
