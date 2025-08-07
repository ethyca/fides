import {
  AntButton as Button,
  AntMessage as message,
  AntTypography as Typography,
  Box,
  Flex,
  Text,
  useDisclosure,
  WarningIcon,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import {
  useGetManualTaskConfigQuery,
  useUpdateDependencyConditionsMutation,
} from "~/features/datastore-connections/connection-manual-tasks.slice";
import { ConditionGroup, ConditionLeaf, GroupOperator } from "~/types/api";

import AddEditConditionModal from "./AddEditConditionModal";
import ConditionsList from "./ConditionsList";

const { Paragraph } = Typography;

interface TaskCreationConditionsProps {
  connectionKey: string;
}

// Custom hook for shared save logic
const useSaveConditions = (
  connectionKey: string,
  updateConditions: ReturnType<typeof useUpdateDependencyConditionsMutation>[0],
  refetch: () => void,
) => {
  const saveConditions = useCallback(
    async (updatedConditions: ConditionLeaf[]) => {
      const conditionGroup: ConditionGroup = {
        logical_operator: GroupOperator.AND,
        conditions: updatedConditions,
      };

      await updateConditions({
        connectionKey,
        conditions: [conditionGroup],
      }).unwrap();

      await refetch();
    },
    [connectionKey, updateConditions, refetch],
  );

  return saveConditions;
};

const TaskCreationConditions = ({
  connectionKey,
}: TaskCreationConditionsProps) => {
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
    async (newCondition: ConditionLeaf) => {
      const originalConditions = conditions; // Capture current state
      let updatedConditions: ConditionLeaf[] = [];

      if (editingIndex !== null) {
        // Update existing condition
        updatedConditions = originalConditions.map((condition, i) =>
          i === editingIndex ? newCondition : condition,
        );
      } else {
        // Add new condition
        // Check if a condition with the same field_address and operator already exists
        const isDuplicate = originalConditions.some(
          (condition) =>
            condition.field_address === newCondition.field_address &&
            condition.operator === newCondition.operator,
        );

        if (isDuplicate) {
          message.warning(
            `A condition for "${newCondition.field_address}" with operator "${newCondition.operator}" already exists.`,
          );
          return;
        }

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
      } catch (err) {
        message.error("Failed to save condition. Please try again.");
        // Revert to captured original state
        setConditions(originalConditions);
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
      <Box className="py-4">
        <Text color="gray.500">Loading conditions...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Box className="py-4">
        <Text color="red.500">
          Failed to load conditions. Please refresh the page and try again.
        </Text>
      </Box>
    );
  }

  return (
    <Box>
      <Flex direction="column" gap={4}>
        <Box>
          <Typography.Title level={5}>
            Conditional task creation
          </Typography.Title>
          <Paragraph className="mt-2 w-2/3 text-gray-600">
            Configure conditions that must be met before a task is created. If
            no conditions are set, manual tasks will be created for every
            incoming privacy request of the corresponding type (access or
            erasure).
          </Paragraph>
          <Paragraph className="mt-2 text-gray-600" strong>
            All conditions must be met for the task to be created.
          </Paragraph>
        </Box>

        <Flex justify="flex-end" align="center" gap={2}>
          <Button type="primary" onClick={handleOpenAddModal}>
            Add condition
          </Button>
        </Flex>

        <ConditionsList
          conditions={conditions}
          onEdit={handleOpenEditModal}
          onDelete={handleDeleteCondition}
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
            <Text color="gray.500">
              Are you sure you want to delete the condition for &ldquo;
              {conditionToDelete?.condition.field_address}&rdquo;? This action
              cannot be undone.
            </Text>
          }
          continueButtonText="Delete"
          isCentered
          icon={<WarningIcon />}
        />
      </Flex>
    </Box>
  );
};

export default TaskCreationConditions;
