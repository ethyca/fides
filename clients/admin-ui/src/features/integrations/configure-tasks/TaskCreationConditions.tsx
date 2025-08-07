import {
  AntButton as Button,
  AntMessage as message,
  AntTypography as Typography,
  Box,
  Flex,
  Icons,
} from "fidesui";
import { useCallback, useEffect, useState } from "react";

import {
  useGetManualTaskConfigQuery,
  useUpdateDependencyConditionsMutation,
} from "~/features/datastore-connections/connection-manual-tasks.slice";
import { ConditionGroup, ConditionLeaf, GroupOperator } from "~/types/api";

import AddConditionForm from "./AddConditionForm";
import ConditionsList from "./ConditionsList";

const { Text, Paragraph } = Typography;

interface TaskCreationConditionsProps {
  connectionKey: string;
}

const TaskCreationConditions = ({
  connectionKey,
}: TaskCreationConditionsProps) => {
  const [conditions, setConditions] = useState<ConditionLeaf[]>([]);
  const [isAddingCondition, setIsAddingCondition] = useState(false);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);

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

  const handleSaveConditions = useCallback(async () => {
    setIsSaving(true);
    try {
      const conditionGroup: ConditionGroup = {
        logical_operator: GroupOperator.AND,
        conditions,
      };

      await updateConditions({
        connectionKey,
        conditions: conditions.length > 0 ? [conditionGroup] : [],
      }).unwrap();

      message.success("Task creation conditions saved successfully!");
      refetch();
    } catch (err) {
      message.error("Failed to save conditions. Please try again.");
    } finally {
      setIsSaving(false);
    }
  }, [conditions, connectionKey, updateConditions, refetch]);

  const handleAddCondition = useCallback((newCondition: ConditionLeaf) => {
    setConditions((prev) => {
      // Check if a condition with the same field_address and operator already exists
      const isDuplicate = prev.some(
        (condition) =>
          condition.field_address === newCondition.field_address &&
          condition.operator === newCondition.operator,
      );

      if (isDuplicate) {
        message.warning(
          `A condition for "${newCondition.field_address}" with operator "${newCondition.operator}" already exists.`,
        );
        return prev;
      }

      return [...prev, newCondition];
    });
    setIsAddingCondition(false);
  }, []);

  const handleEditCondition = useCallback((index: number) => {
    setEditingIndex(index);
    setIsAddingCondition(true);
  }, []);

  const handleUpdateCondition = useCallback(
    (updatedCondition: ConditionLeaf) => {
      if (editingIndex !== null) {
        setConditions((prev) =>
          prev.map((condition, i) =>
            i === editingIndex ? updatedCondition : condition,
          ),
        );
      }
      setEditingIndex(null);
      setIsAddingCondition(false);
    },
    [editingIndex],
  );

  const handleDeleteCondition = useCallback((index: number) => {
    setConditions((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const handleCancelAdd = useCallback(() => {
    setIsAddingCondition(false);
    setEditingIndex(null);
  }, []);

  if (isLoading) {
    return (
      <Box className="py-4">
        <Text type="secondary">Loading conditions...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Box className="py-4">
        <Text type="danger">
          Failed to load conditions. Please refresh the page and try again.
        </Text>
      </Box>
    );
  }

  return (
    <Box>
      <Flex direction="column" gap={4}>
        <Box>
          <Text strong className="text-lg">
            Task creation conditions
          </Text>
          <Paragraph className="mt-2 w-2/3 text-gray-600">
            Configure conditions that must be met before a task is created. If
            no conditions are set, manual tasks will be created for every
            incoming privacy request of the corresponding type (access or
            erasure). All conditions must be met (AND logic).
          </Paragraph>
        </Box>

        <ConditionsList
          conditions={conditions}
          onEdit={handleEditCondition}
          onDelete={handleDeleteCondition}
        />

        {isAddingCondition ? (
          <AddConditionForm
            onAdd={
              editingIndex !== null ? handleUpdateCondition : handleAddCondition
            }
            onCancel={handleCancelAdd}
            editingCondition={
              editingIndex !== null ? conditions[editingIndex] : undefined
            }
          />
        ) : (
          <Flex justify="space-between" align="center" className="mt-2">
            <Button
              type="dashed"
              onClick={() => setIsAddingCondition(true)}
              className="min-w-32"
              icon={<Icons.Add />}
            >
              Add Condition
            </Button>

            {conditions.length > 0 && (
              <Button
                type="primary"
                onClick={handleSaveConditions}
                loading={isSaving}
                className="min-w-32"
              >
                Save Conditions
              </Button>
            )}
          </Flex>
        )}
      </Flex>
    </Box>
  );
};

export default TaskCreationConditions;
