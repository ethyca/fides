import { useCallback, useMemo, useState } from "react";

import { StagedResourceAPIResponse } from "~/types/api";

interface UseInfrastructureSystemsSelectionConfig<
  T extends StagedResourceAPIResponse,
> {
  items: T[] | undefined;
  getRecordKey: (item: T) => string;
}

export const useInfrastructureSystemsSelection = <
  T extends StagedResourceAPIResponse,
>({
  items,
  getRecordKey,
}: UseInfrastructureSystemsSelectionConfig<T>) => {
  const [selectedKeys, setSelectedKeys] = useState<Set<string>>(new Set());

  const hasSelectedRows = selectedKeys.size > 0;
  const selectedRowsCount = selectedKeys.size;

  const handleSelectAll = useCallback(
    (checked: boolean) => {
      if (checked) {
        const allKeys = new Set(items?.map((item) => getRecordKey(item)) ?? []);
        setSelectedKeys(allKeys);
      } else {
        setSelectedKeys(new Set());
      }
    },
    [items, getRecordKey],
  );

  const handleSelectItem = useCallback((key: string, selected: boolean) => {
    setSelectedKeys((prev) => {
      const next = new Set(prev);
      if (selected) {
        next.add(key);
      } else {
        next.delete(key);
      }
      return next;
    });
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedKeys(new Set());
  }, []);

  const isAllSelected = useMemo(() => {
    if (!items || items.length === 0) {
      return false;
    }
    return (
      selectedKeys.size > 0 &&
      selectedKeys.size === items.length &&
      items.every((item) => selectedKeys.has(getRecordKey(item)))
    );
  }, [items, selectedKeys, getRecordKey]);

  const isIndeterminate = useMemo(() => {
    if (!items || items.length === 0) {
      return false;
    }
    return selectedKeys.size > 0 && selectedKeys.size < items.length;
  }, [items, selectedKeys]);

  const selectedItems = useMemo(() => {
    if (!items) {
      return [];
    }
    return items.filter((item) => selectedKeys.has(getRecordKey(item)));
  }, [items, selectedKeys, getRecordKey]);

  const isItemSelected = useCallback(
    (item: T) => {
      return selectedKeys.has(getRecordKey(item));
    },
    [selectedKeys, getRecordKey],
  );

  return {
    selectedKeys,
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
