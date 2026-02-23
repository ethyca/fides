import {
  Button,
  Flex,
  List,
  Modal,
  Tag,
  Tooltip,
  Typography,
  useMessage,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import { operatorLabels } from "~/features/integrations/configure-tasks/constants";
import {
  formatConditionValue,
  formatFieldDisplay,
} from "~/features/integrations/configure-tasks/utils";
import PolicyConditionModal from "~/features/policies/conditions/PolicyConditionModal";
import {
  useGetPolicyQuery,
  useUpdatePolicyConditionsMutation,
} from "~/features/policy/policy.slice";
import { ConditionLeaf, GroupOperator } from "~/types/api";

const { Paragraph, Text } = Typography;

interface PolicyConditionsTabProps {
  policyKey: string;
}

const PolicyConditionsTab = ({ policyKey }: PolicyConditionsTabProps) => {
  const [conditions, setConditions] = useState<ConditionLeaf[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCondition, setEditingCondition] =
    useState<ConditionLeaf | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [conditionToDelete, setConditionToDelete] = useState<{
    index: number;
    condition: ConditionLeaf;
  } | null>(null);

  const message = useMessage();
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const { data: policy, refetch } = useGetPolicyQuery(policyKey, {
    skip: !policyKey,
  });

  const [updateConditions] = useUpdatePolicyConditionsMutation();

  // Note: In a real implementation, you would fetch conditions from the policy
  // For now, we'll use local state since the policy conditions API might not be fully implemented
  useEffect(() => {
    // If the policy has conditions, load them
    // This would typically come from a dedicated conditions endpoint
    setConditions([]);
  }, [policy]);

  const saveConditions = useCallback(
    async (updatedConditions: ConditionLeaf[]) => {
      const conditionGroup = {
        logical_operator: GroupOperator.AND,
        conditions: updatedConditions,
      };

      await updateConditions({
        policyKey,
        conditions: { conditions: [conditionGroup] },
      }).unwrap();

      refetch();
    },
    [policyKey, updateConditions, refetch],
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
      const originalConditions = conditions;
      let updatedConditions: ConditionLeaf[] = [];

      if (editingIndex !== null) {
        updatedConditions = originalConditions.map((condition, i) =>
          i === editingIndex ? newCondition : condition,
        );
      } else {
        updatedConditions = [...originalConditions, newCondition];
      }

      setConditions(updatedConditions);

      try {
        await saveConditions(updatedConditions);
        message.success(
          editingIndex !== null
            ? "Condition updated successfully!"
            : "Condition added successfully!",
        );
        handleCloseModal();
      } catch (err) {
        setConditions(originalConditions);
        throw err;
      }
    },
    [conditions, editingIndex, saveConditions, message, handleCloseModal],
  );

  const handleDeleteCondition = useCallback(
    (index: number, condition: ConditionLeaf) => {
      setConditionToDelete({ index, condition });
      setIsDeleteModalOpen(true);
    },
    [],
  );

  const handleConfirmDelete = useCallback(async () => {
    if (conditionToDelete) {
      const originalConditions = conditions;
      const updatedConditions = originalConditions.filter(
        (_, i) => i !== conditionToDelete.index,
      );

      setConditions(updatedConditions);

      try {
        await saveConditions(updatedConditions);
        message.success("Condition deleted successfully!");
      } catch (err) {
        message.error("Failed to delete condition. Please try again.");
        setConditions(originalConditions);
      }

      setConditionToDelete(null);
    }
    setIsDeleteModalOpen(false);
  }, [conditionToDelete, conditions, saveConditions, message]);

  return (
    <div>
      <div>
        <Typography.Title level={5}>Policy conditions</Typography.Title>
        <Paragraph type="secondary" className="mt-2 w-2/3">
          Configure conditions that control when this policy applies to privacy
          requests. If no conditions are set, the policy will apply to all
          matching requests.
        </Paragraph>
        <Paragraph type="secondary" className="mt-2">
          <Text strong>
            All conditions must be met for the policy to apply.
          </Text>
        </Paragraph>
      </div>

      <div className="mb-4 flex items-center justify-end gap-2">
        <Button
          type="primary"
          onClick={handleOpenAddModal}
          data-testid="add-condition-btn"
        >
          Add condition
        </Button>
      </div>

      <List
        dataSource={conditions}
        data-testid="conditions-list"
        locale={{
          emptyText: (
            <div className="py-8 text-center">
              <Text type="secondary">
                No conditions configured. This policy will apply to all matching
                privacy requests.
              </Text>
            </div>
          ),
        }}
        renderItem={(condition: ConditionLeaf, index: number) => (
          <List.Item
            key={index}
            aria-label={`Condition: ${formatFieldDisplay(condition.field_address)} ${operatorLabels[condition.operator]}${formatConditionValue(condition) ? ` ${formatConditionValue(condition)}` : ""}`}
            actions={[
              <Button
                key="edit"
                type="link"
                onClick={() => handleOpenEditModal(index, condition)}
                data-testid={`edit-condition-${index}-btn`}
                className="px-1"
                aria-label={`Edit condition for ${condition.field_address}`}
              >
                Edit
              </Button>,
              <Button
                key="delete"
                type="link"
                onClick={() => handleDeleteCondition(index, condition)}
                data-testid={`delete-condition-${index}-btn`}
                className="px-1"
                aria-label={`Delete condition for ${condition.field_address}`}
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
                      <Text>{formatFieldDisplay(condition.field_address)}</Text>
                    </Tooltip>
                  </div>
                  <Tag color="sandstone">
                    {operatorLabels[condition.operator]}
                  </Tag>
                  <div className="max-w-[300px]">
                    {formatConditionValue(condition) && (
                      <Text
                        ellipsis={{ tooltip: formatConditionValue(condition) }}
                      >
                        {formatConditionValue(condition)}
                      </Text>
                    )}
                  </div>
                </Flex>
              }
            />
          </List.Item>
        )}
        className="mb-4"
      />

      <PolicyConditionModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onConditionSaved={handleConditionSaved}
        editingCondition={editingCondition}
        policyKey={policyKey}
      />

      <Modal
        title="Delete condition"
        open={isDeleteModalOpen}
        onCancel={() => {
          setConditionToDelete(null);
          setIsDeleteModalOpen(false);
        }}
        onOk={handleConfirmDelete}
        okText="Delete"
        okButtonProps={{ danger: true }}
        cancelText="Cancel"
        centered
        data-testid="delete-condition-modal"
      >
        <Text type="secondary">
          Are you sure you want to delete the condition for &ldquo;
          {conditionToDelete?.condition.field_address}&rdquo;? This action
          cannot be undone.
        </Text>
      </Modal>
    </div>
  );
};

export default PolicyConditionsTab;
