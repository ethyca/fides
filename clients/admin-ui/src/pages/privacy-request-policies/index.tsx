import {
  Button,
  Empty,
  Flex,
  List,
  Modal,
  Skeleton,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import { uniqBy } from "lodash";
import type { NextPage } from "next";
import { useCallback, useMemo, useState } from "react";

import Layout from "~/features/common/Layout";
import { POLICY_DETAIL_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import SearchInput from "~/features/common/SearchInput";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import {
  useDeletePolicyMutation,
  useGetPoliciesQuery,
} from "~/features/policies/policy.slice";
import { PolicyFormModal } from "~/features/policies/PolicyFormModal";
import { PolicyResponse } from "~/types/api";

const { Paragraph, Text } = Typography;

const PoliciesPage: NextPage = () => {
  const message = useMessage();
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [policyToEdit, setPolicyToEdit] = useState<PolicyResponse | null>(null);
  const [policyToDelete, setPolicyToDelete] = useState<PolicyResponse | null>(
    null,
  );

  const { data: policiesData, isLoading } = useGetPoliciesQuery();
  const [deletePolicy] = useDeletePolicyMutation();

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

  const handleEdit = useCallback((policy: PolicyResponse) => {
    setPolicyToEdit(policy);
  }, []);

  const handleConfirmDelete = useCallback(async () => {
    if (!policyToDelete?.key) {
      return;
    }
    try {
      await deletePolicy(policyToDelete.key).unwrap();
      message.success("Policy deleted successfully");
    } catch {
      message.error("Failed to delete policy");
    }
    setPolicyToDelete(null);
  }, [policyToDelete, deletePolicy, message]);

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
                      onClick={() => setPolicyToDelete(policy)}
                      data-testid={`delete-policy-${policy.key}-btn`}
                    >
                      Delete
                    </Button>,
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

      <PolicyFormModal
        isOpen={isCreateModalOpen || !!policyToEdit}
        onClose={() => {
          setIsCreateModalOpen(false);
          setPolicyToEdit(null);
        }}
        policyKey={policyToEdit?.key ?? undefined}
      />

      <Modal
        title="Delete policy"
        open={!!policyToDelete}
        onCancel={() => setPolicyToDelete(null)}
        onOk={handleConfirmDelete}
        okText="Delete"
        okButtonProps={{ danger: true }}
        cancelText="Cancel"
        centered
        data-testid="delete-policy-modal"
      >
        <Text type="secondary">
          Are you sure you want to delete the policy &ldquo;
          {policyToDelete?.name}&rdquo;? This action cannot be undone and will
          also delete all associated rules.
        </Text>
      </Modal>
    </Layout>
  );
};

export default PoliciesPage;
