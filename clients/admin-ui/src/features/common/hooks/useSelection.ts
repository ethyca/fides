import { useCallback, useState } from "react";

/**
 * A reusable hook for managing selection state.
 * Remember to call clearSelectedIds when the data changes.
 * @returns Object containing selectedIds, setSelectedIds, and clearSelectedIds
 */
export const useSelection = () => {
  const [selectedIds, setSelectedIds] = useState<React.Key[]>([]);

  // Use this function to clear the selected ids when the data changes / actions are performed
  const clearSelectedIds = useCallback(() => {
    setSelectedIds([]);
  }, []);

  return {
    selectedIds,
    setSelectedIds,
    clearSelectedIds,
  };
};
