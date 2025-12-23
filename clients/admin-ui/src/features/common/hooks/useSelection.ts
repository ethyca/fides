import { useCallback, useMemo, useState } from "react";

export type CheckboxSelectState = "checked" | "unchecked" | "indeterminate";

interface UseSelectionOptions {
  /**
   * Optional array of keys for items on the current page.
   * When provided, enables select all results in the current page functionality.
   */
  currentPageKeys?: React.Key[];
}

/**
 * A reusable hook for managing selection state.
 * Remember to call clearSelectedIds when the data changes.
 * @param options - Optional configuration including currentPageKeys for select all support
 * @returns Object containing selectedIds, setSelectedIds, clearSelectedIds, and optionally checkboxSelectState and handleSelectAll
 */
export const useSelection = (options?: UseSelectionOptions) => {
  const { currentPageKeys } = options ?? {};
  const [selectedIds, setSelectedIds] = useState<React.Key[]>([]);

  // Use this function to clear the selected ids when the data changes / actions are performed
  const clearSelectedIds = useCallback(() => {
    setSelectedIds([]);
  }, []);

  // Calculate checkbox state for select all functionality
  const checkboxSelectState: CheckboxSelectState = useMemo(() => {
    if (!currentPageKeys || currentPageKeys.length === 0) {
      return "unchecked";
    }

    const allSelected = currentPageKeys.every((key) =>
      selectedIds.includes(key),
    );
    if (allSelected) {
      return "checked";
    }

    const someSelected =
      selectedIds.length > 0 &&
      currentPageKeys.some((key) => selectedIds.includes(key));
    if (someSelected) {
      return "indeterminate";
    }

    return "unchecked";
  }, [currentPageKeys, selectedIds]);

  // Handler for select all checkbox
  const handleSelectAll = useCallback(
    (checked: boolean) => {
      if (!currentPageKeys) {
        return;
      }

      if (checked) {
        // Select all on current page
        const newSelected = [...new Set([...selectedIds, ...currentPageKeys])];
        setSelectedIds(newSelected);
      } else {
        // Deselect all on current page
        const currentPageKeysSet = new Set<React.Key>(currentPageKeys);
        setSelectedIds(selectedIds.filter((id) => !currentPageKeysSet.has(id)));
      }
    },
    [selectedIds, currentPageKeys],
  );

  return {
    selectedIds,
    setSelectedIds,
    clearSelectedIds,
    checkboxSelectState,
    handleSelectAll,
  };
};
