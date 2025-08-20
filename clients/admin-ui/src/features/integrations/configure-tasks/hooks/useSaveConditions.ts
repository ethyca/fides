import { useCallback } from "react";

import { useUpdateDependencyConditionsMutation } from "~/features/datastore-connections/connection-manual-tasks.slice";
import { ConditionGroup, ConditionLeaf, GroupOperator } from "~/types/api";

/**
 * Custom hook for saving task creation conditions
 */
export const useSaveConditions = (
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
