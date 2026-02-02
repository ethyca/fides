import { useCallback, useEffect, useMemo, useState } from "react";

import { StagedResourceAPIResponse } from "~/types/api";
import { DiffStatus } from "~/types/api/models/DiffStatus";

type SelectionMode = "explicit" | "all";

interface InfrastructureSystemsFilters {
  search?: string;
  diff_status?: DiffStatus | DiffStatus[];
  vendor_id?: string | string[];
  data_uses?: string[];
}

interface UseInfrastructureSystemsSelectionConfig<
  T extends StagedResourceAPIResponse,
> {
  items: T[] | undefined;
  getRecordKey: (item: T) => string;
  totalCount?: number;
  filters?: InfrastructureSystemsFilters;
}

export const useInfrastructureSystemsSelection = <
  T extends StagedResourceAPIResponse,
>({
  items,
  getRecordKey,
  totalCount = 0,
  filters,
}: UseInfrastructureSystemsSelectionConfig<T>) => {
  const [selectionMode, setSelectionMode] = useState<SelectionMode>("explicit");
  const [excludedKeys, setExcludedKeys] = useState<Set<string>>(new Set());
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

  // Clear selection when filters change (user changed search/filters)
  useEffect(() => {
    setSelectionMode("explicit");
    setExcludedKeys(new Set());
    setSelectedKeys(new Set());
  }, [
    filters?.search,
    filters?.diff_status,
    filters?.vendor_id,
    filters?.data_uses,
  ]);

  const hasSelectedRows = useMemo(() => {
    if (selectionMode === "all") {
      return excludedKeys.size < (totalCount || 0);
    }
    return selectedKeys.size > 0;
  }, [selectionMode, excludedKeys.size, selectedKeys.size, totalCount]);

  const selectedRowsCount = useMemo(() => {
    if (selectionMode === "all") {
      return totalCount - excludedKeys.size;
    }
    return selectedKeys.size;
  }, [selectionMode, excludedKeys.size, selectedKeys.size, totalCount]);

  const handleSelectAll = useCallback((checked: boolean) => {
    if (checked) {
      // Switch to "all" mode - select all items matching current filters
      setSelectionMode("all");
      setExcludedKeys(new Set());
      setSelectedKeys(new Set());
    } else {
      // Switch back to explicit mode and clear selection
      setSelectionMode("explicit");
      setExcludedKeys(new Set());
      setSelectedKeys(new Set());
    }
  }, []);

  const handleSelectItem = useCallback(
    (key: string, selected: boolean) => {
      if (selectionMode === "all") {
        // In "all" mode, toggle exclusions
        // Find the item to get its URN for exclusion tracking
        const targetItem = items?.find((i) => getRecordKey(i) === key);
        if (!targetItem?.urn) {
          // If no URN, can't exclude (shouldn't happen in practice)
          return;
        }
        setExcludedKeys((prev) => {
          const next = new Set(prev);
          if (selected) {
            // Item is being selected, remove from exclusions
            next.delete(targetItem.urn);
          } else {
            // Item is being deselected, add to exclusions
            next.add(targetItem.urn);
          }
          return next;
        });
      } else {
        // In explicit mode, toggle selected keys
        setSelectedKeys((prev) => {
          const next = new Set(prev);
          if (selected) {
            next.add(key);
          } else {
            next.delete(key);
          }
          return next;
        });
      }
    },
    [selectionMode, items, getRecordKey],
  );

  const clearSelection = useCallback(() => {
    setSelectionMode("explicit");
    setExcludedKeys(new Set());
    setSelectedKeys(new Set());
  }, []);

  const isAllSelected = useMemo(() => {
    if (!items || items.length === 0) {
      return false;
    }
    if (selectionMode === "all") {
      // In "all" mode, check if current page items are all included (none excluded by URN)
      return items.every((item) => !item.urn || !excludedKeys.has(item.urn));
    }
    // In explicit mode, check if all current page items are selected
    return (
      selectedKeys.size > 0 &&
      selectedKeys.size === items.length &&
      items.every((item) => selectedKeys.has(getRecordKey(item)))
    );
  }, [items, selectedKeys, excludedKeys, selectionMode, getRecordKey]);

  const isIndeterminate = useMemo(() => {
    if (!items || items.length === 0) {
      return false;
    }
    if (selectionMode === "all") {
      // In "all" mode, indeterminate if some items on current page are excluded by URN
      const currentPageExcluded = items.filter(
        (item) => item.urn && excludedKeys.has(item.urn),
      ).length;
      return currentPageExcluded > 0 && currentPageExcluded < items.length;
    }
    // In explicit mode, indeterminate if some but not all items are selected
    return selectedKeys.size > 0 && selectedKeys.size < items.length;
  }, [items, selectedKeys, excludedKeys, selectionMode]);

  const selectedItems = useMemo(() => {
    if (!items) {
      return [];
    }
    if (selectionMode === "all") {
      // In "all" mode, return items that are not excluded by URN
      return items.filter((item) => !item.urn || !excludedKeys.has(item.urn));
    }
    // In explicit mode, return explicitly selected items
    return items.filter((item) => selectedKeys.has(getRecordKey(item)));
  }, [items, selectedKeys, excludedKeys, selectionMode, getRecordKey]);

  const isItemSelected = useCallback(
    (item: T) => {
      if (selectionMode === "all") {
        // In "all" mode, item is selected if it's not excluded by URN
        return !item.urn || !excludedKeys.has(item.urn);
      }
      // In explicit mode, check if key is in selectedKeys
      const key = getRecordKey(item);
      return selectedKeys.has(key);
    },
    [selectedKeys, excludedKeys, selectionMode, getRecordKey],
  );

  // Return excluded URNs as array for use in bulk actions
  const excludedUrns = useMemo(() => {
    return Array.from(excludedKeys);
  }, [excludedKeys]);

  return {
    selectedKeys,
    excludedKeys,
    excludedUrns,
    selectionMode,
    hasSelectedRows,
    selectedRowsCount,
    selectedItems,
    isAllSelected,
    isIndeterminate,
    handleSelectAll,
    handleSelectItem,
    clearSelection,
    isItemSelected,
  };
};
