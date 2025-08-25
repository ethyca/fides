import {
  AntButton as Button,
  AntFlex as Flex,
  AntList as List,
  AntMessage as message,
  AntTag as Tag,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  useDisclosure,
  WarningIcon,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import {
  useGetManualTaskConfigQuery,
  useUpdateDependencyConditionsMutation,
} from "~/features/datastore-connections/connection-manual-tasks.slice";
import { ConditionLeaf } from "~/types/api";

import AddEditConditionModal from "./AddEditConditionModal";
import { operatorLabels } from "./constants";
import { useSaveConditions } from "./hooks/useSaveConditions";

const { Paragraph, Text } = Typography;

interface TaskConditionsTabProps {
  connectionKey: string;
}

const TaskConditionsTab = ({ connectionKey }: TaskConditionsTabProps) => {
  const [conditions, setConditions] = useState<ConditionLeaf[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingCondition, setEditingCondition] =
    useState<ConditionLeaf | null>(null);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [conditionToDelete, setConditionToDelete] = useState<{
    index: number;
    condition: ConditionLeaf;
  } | null>(null);

  const {
    isOpen: isDeleteOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const {
    data: manualTaskConfig,
    isLoading,
    error,
    refetch,
  } = useGetManualTaskConfigQuery(
    { connectionKey },
    {
      skip: !connectionKey,
    },
  );

  const [updateConditions] = useUpdateDependencyConditionsMutation();
  const saveConditions = useSaveConditions(
    connectionKey,
    updateConditions,
    refetch,
  );

  // Extract conditions from dependency_conditions field in ManualTaskResponse
  useEffect(() => {
    if (
      manualTaskConfig?.dependency_conditions &&
      manualTaskConfig.dependency_conditions.length > 0
    ) {
      const firstGroup = manualTaskConfig.dependency_conditions[0];
      // Filter to only ConditionLeaf items (not nested groups)
      const leafConditions = firstGroup.conditions.filter(
        (condition): condition is ConditionLeaf =>
          "field_address" in condition && "operator" in condition,
      );
      setConditions(leafConditions);
    } else {
      setConditions([]);
    }
  }, [manualTaskConfig]);

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
      const originalConditions = conditions; // Capture current state
      let updatedConditions: ConditionLeaf[] = [];

      if (editingIndex !== null) {
        // Update existing condition
        updatedConditions = originalConditions.map((condition, i) =>
          i === editingIndex ? newCondition : condition,
        );
      } else {
        // Add new condition
        updatedConditions = [...originalConditions, newCondition];
      }

      // Update local state optimistically
      setConditions(updatedConditions);

      // Auto-save to backend
      try {
        await saveConditions(updatedConditions);
        message.success(
          editingIndex !== null
            ? "Condition updated successfully!"
            : "Condition added successfully!",
        );
        // Close modal is now handled by the modal itself on success
      } catch (err) {
        // Revert to captured original state
        setConditions(originalConditions);
        // Re-throw the error to be handled by the modal
        throw err;
      }
    },
    [editingIndex, conditions, saveConditions],
  );

  const handleDeleteCondition = useCallback(
    (index: number, condition: ConditionLeaf) => {
      setConditionToDelete({ index, condition });
      onDeleteOpen();
    },
    [onDeleteOpen],
  );

  const handleConfirmDelete = useCallback(async () => {
    if (conditionToDelete) {
      const originalConditions = conditions; // Capture current state
      const updatedConditions = originalConditions.filter(
        (_, i) => i !== conditionToDelete.index,
      );

      // Update local state optimistically
      setConditions(updatedConditions);

      // Auto-save to backend
      try {
        await saveConditions(updatedConditions);
        message.success("Condition deleted successfully!");
      } catch (err) {
        message.error("Failed to delete condition. Please try again.");
        // Revert to captured original state
        setConditions(originalConditions);
      }

      setConditionToDelete(null);
    }
    onDeleteClose();
  }, [conditionToDelete, conditions, saveConditions, onDeleteClose]);

  if (isLoading) {
    return (
      <div className="py-4">
        <Text className="text-gray-500">Loading conditions...</Text>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-4">
        <Text className="text-red-500">
          Failed to load conditions. Please refresh the page and try again.
        </Text>
      </div>
    );
  }

  return (
    <div>
      <div>
        <Typography.Title level={5}>Conditional task creation</Typography.Title>
        <Paragraph className="mt-2 w-2/3 text-gray-600">
          Configure conditions that must be met before a task is created. If no
          conditions are set, manual tasks will be created for every incoming
          privacy request of the corresponding type (access or erasure).
        </Paragraph>
        <Paragraph className="mt-2 text-gray-600">
          <Text strong>
            All conditions must be met for the task to be created.
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
        locale={{
          emptyText: (
            <div className="py-8 text-center">
              <Text type="secondary">
                No conditions configured. Manual tasks will be created for all
                privacy requests.
              </Text>
            </div>
          ),
        }}
        renderItem={(condition: ConditionLeaf, index: number) => (
          <List.Item
            key={index}
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
                      <Text>{condition.field_address.split(":").pop()}</Text>
                    </Tooltip>
                  </div>
                  <Tag color="sandstone">
                    {operatorLabels[condition.operator]}
                  </Tag>
                  <div className="max-w-[300px]">
                    {condition.value !== null &&
                      condition.value !== undefined && (
                        <Text ellipsis={{ tooltip: String(condition.value) }}>
                          {String(condition.value)}
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

      <AddEditConditionModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onConditionSaved={handleConditionSaved}
        editingCondition={editingCondition}
      />

      <ConfirmationModal
        isOpen={isDeleteOpen}
        onClose={() => {
          setConditionToDelete(null);
          onDeleteClose();
        }}
        onConfirm={handleConfirmDelete}
        title="Delete condition"
        message={
          <Text className="text-gray-500">
            Are you sure you want to delete the condition for &ldquo;
            {conditionToDelete?.condition.field_address}&rdquo;? This action
            cannot be undone.
          </Text>
        }
        continueButtonText="Delete"
        isCentered
        icon={<WarningIcon />}
      />
    </div>
  );
};

export default TaskConditionsTab;
