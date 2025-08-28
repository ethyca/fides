import { useCallback } from "react";

import { useUpdateDependencyConditionsMutation } from "~/features/datastore-connections/connection-manual-tasks.slice";
import { ConditionLeaf, GroupOperator } from "~/types/api";

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
      // If no conditions, send empty array instead of empty group
      const conditions =
        updatedConditions.length === 0
          ? []
          : [
              {
                logical_operator: GroupOperator.AND,
                conditions: updatedConditions,
              },
            ];

      await updateConditions({
        connectionKey,
        conditions,
      }).unwrap();

      await refetch();
    },
    [connectionKey, updateConditions, refetch],
  );

  return saveConditions;
};
