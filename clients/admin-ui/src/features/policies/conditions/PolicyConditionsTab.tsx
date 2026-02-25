import {
  Button,
  Empty,
  Flex,
  List,
  Modal,
  Tag,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useEffect, useMemo, useState } from "react";

import { operatorLabels } from "~/features/integrations/configure-tasks/constants";
import {
  formatConditionValue,
  formatFieldDisplay,
} from "~/features/integrations/configure-tasks/utils";
import { useUpdatePolicyConditionsMutation } from "~/features/policies/policy.slice";
import { extractLeafConditions } from "~/features/policies/utils/extractLeafConditions";
import type { ConditionGroup, ConditionLeaf, GroupOperator } from "~/types/api";
import { GroupOperator as GroupOp } from "~/types/api";

import { AddEditPolicyConditionModal } from "./AddEditPolicyConditionModal";

const { Title, Paragraph, Text } = Typography;

/**
 * Assembles a condition tree from a flat array of leaf conditions.
 * - 0 leaves -> null (no conditions)
 * - 1 leaf   -> the leaf itself (no group wrapper)
 * - 2+ leaves -> ConditionGroup with AND operator
 */
const assembleConditionTree = (
  leaves: ConditionLeaf[],
): ConditionLeaf | ConditionGroup | null => {
  if (leaves.length === 0) {
    return null;
  }
  if (leaves.length === 1) {
    return leaves[0];
  }
  return {
    logical_operator: GroupOp.AND as GroupOperator,
    conditions: leaves,
  };
};

interface PolicyConditionsTabProps {
  conditions?: ConditionGroup | ConditionLeaf | null;
  policyKey: string;
}

export const PolicyConditionsTab = ({
  conditions,
  policyKey,
}: PolicyConditionsTabProps) => {
  const message = useMessage();
  const [modalApi, modalContext] = Modal.useModal();
  const [updatePolicyConditions] = useUpdatePolicyConditionsMutation();

  const serverLeafConditions = useMemo(
    () => extractLeafConditions(conditions),
    [conditions],
  );

  const [leafConditions, setLeafConditions] = useState<ConditionLeaf[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCondition, setEditingCondition] =
    useState<ConditionLeaf | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  useEffect(() => {
    setLeafConditions(serverLeafConditions);
  }, [serverLeafConditions]);

  const saveConditions = useCallback(
    async (leaves: ConditionLeaf[]) => {
      const condition = assembleConditionTree(leaves);
      await updatePolicyConditions({ policyKey, condition }).unwrap();
    },
    [policyKey, updatePolicyConditions],
  );

  const handleOpenAddModal = useCallback(() => {
    setEditingCondition(null);
    setEditingIndex(null);
    setIsModalOpen(true);
  }, []);

  const handleOpenEditModal = useCallback(
    (index: number, condition: ConditionLeaf) => {
      setEditingCondition(condition);
      setEditingIndex(index);
      setIsModalOpen(true);
    },
    [],
  );

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setEditingCondition(null);
    setEditingIndex(null);
  }, []);

  const handleConditionSaved = useCallback(
    async (newCondition: ConditionLeaf): Promise<void> => {
      const original = leafConditions;
      const updated =
        editingIndex !== null
          ? original.map((c, i) => (i === editingIndex ? newCondition : c))
          : [...original, newCondition];

      setLeafConditions(updated);

      try {
        await saveConditions(updated);
        message.success(
          editingIndex !== null
            ? "Condition updated successfully!"
            : "Condition added successfully!",
        );
      } catch (e) {
        setLeafConditions(original);
        message.error("Failed to save condition. Please try again.");
        throw e;
      }
    },
    [leafConditions, editingIndex, saveConditions, message],
  );

  const handleDeleteCondition = useCallback(
    (index: number, condition: ConditionLeaf) => {
      modalApi.confirm({
        title: "Delete condition",
        icon: null,
        content: (
          <Text type="secondary">
            Are you sure you want to delete the condition for &ldquo;
            {condition.field_address}&rdquo;? This action cannot be undone.
          </Text>
        ),
        okText: "Delete",
        okButtonProps: { danger: true },
        centered: true,
        onOk: async () => {
          const original = leafConditions;
          const updated = original.filter((_, i) => i !== index);

          setLeafConditions(updated);

          try {
            await saveConditions(updated);
            message.success("Condition deleted successfully!");
          } catch {
            setLeafConditions(original);
            message.error("Failed to delete condition. Please try again.");
          }
        },
      });
    },
    [modalApi, leafConditions, saveConditions, message],
  );

  return (
    <>
      <Title level={5} data-testid="policy-conditions-title">
        Policy conditions
      </Title>
      <Paragraph
        type="secondary"
        className="w-2/3"
        data-testid="policy-conditions-description"
      >
        Configure conditions that control when this policy applies to privacy
        requests. If no conditions are set, the policy will apply to all
        matching requests.
      </Paragraph>
      <Paragraph strong data-testid="policy-conditions-note">
        All conditions must be met for the policy to apply.
      </Paragraph>

      <Flex justify="flex-end" className="mb-4">
        <Button
          type="primary"
          onClick={handleOpenAddModal}
          data-testid="add-condition-btn"
        >
          Add condition
        </Button>
      </Flex>

      <List
        dataSource={leafConditions}
        data-testid="conditions-list"
        locale={{
          emptyText: (
            <Empty
              description="No rules configured for this policy"
              className="py-8"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          ),
        }}
        renderItem={(condition: ConditionLeaf, index: number) => {
          const formattedValue = formatConditionValue(condition);
          return (
            <List.Item
              key={index}
              data-testid={`condition-row-${index}`}
              actions={[
                <Button
                  key="edit"
                  type="link"
                  onClick={() => handleOpenEditModal(index, condition)}
                  data-testid={`edit-condition-${index}-btn`}
                  className="px-1"
                >
                  Edit
                </Button>,
                <Button
                  key="delete"
                  type="link"
                  onClick={() => handleDeleteCondition(index, condition)}
                  data-testid={`delete-condition-${index}-btn`}
                  className="px-1"
                >
                  Delete
                </Button>,
              ]}
            >
              <List.Item.Meta
                title={
                  <Flex gap={8} align="center" className="font-normal">
                    <div className="max-w-[300px]">
                      <Tooltip title={condition.field_address}>
                        <Text>
                          {formatFieldDisplay(condition.field_address)}
                        </Text>
                      </Tooltip>
                    </div>
                    <Tag color="sandstone">
                      {operatorLabels[condition.operator]}
                    </Tag>
                    {formattedValue && (
                      <div className="max-w-[300px]">
                        <Text ellipsis={{ tooltip: formattedValue }}>
                          {formattedValue}
                        </Text>
                      </div>
                    )}
                  </Flex>
                }
              />
            </List.Item>
          );
        }}
      />

      <AddEditPolicyConditionModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onConditionSaved={handleConditionSaved}
        editingCondition={editingCondition}
      />

      {modalContext}
    </>
  );
};
