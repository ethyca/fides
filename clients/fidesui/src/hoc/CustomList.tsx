import { Checkbox, List, ListProps } from "antd/lib";
import React, { useCallback, useMemo } from "react";

export interface RowSelection<T> {
  selectedRowKeys?: React.Key[];
  onChange?: (selectedRowKeys: React.Key[], selectedRows: T[]) => void;
  getCheckboxProps?: (record: T) => { disabled?: boolean };
}

export interface CustomListProps<T> extends Omit<ListProps<T>, "renderItem"> {
  rowSelection?: RowSelection<T>;
  renderItem?: (
    item: T,
    index: number,
    checkbox?: React.ReactNode,
  ) => React.ReactNode;
}

const getItemKey = <T,>(item: T, index: number): React.Key => {
  if (item && typeof item === "object" && "key" in item) {
    return (item as { key: React.Key }).key;
  }
  return index;
};

const withCustomProps = (WrappedComponent: typeof List) => {
  const WrappedList = <T,>({
    rowSelection,
    renderItem,
    dataSource,
    ...props
  }: CustomListProps<T>) => {
    // If not using rowSelection or renderItem, render without checkbox enhancement
    if (!renderItem || !rowSelection) {
      return (
        <WrappedComponent
          {...props}
          dataSource={dataSource}
          renderItem={renderItem}
        />
      );
    }

    const { selectedRowKeys = [], onChange, getCheckboxProps } = rowSelection;

    // Create a Set for O(1) lookup of selected keys
    const selectedKeysSet = useMemo(
      () => new Set(selectedRowKeys),
      [selectedRowKeys],
    );

    // Build key-to-item map only when needed for onChange callback
    const keyToDataMap = useMemo(() => {
      if (!onChange || !dataSource) {
        return null;
      }

      const map = new Map<React.Key, T>();
      dataSource.forEach((item, index) => {
        const key = getItemKey(item, index);
        map.set(key, item);
      });
      return map;
    }, [dataSource, onChange]);

    // Handle checkbox selection
    const handleCheckboxChange = useCallback(
      (itemKey: React.Key, checked: boolean) => {
        if (!onChange || !keyToDataMap) {
          return;
        }

        const newSelectedRowKeys = checked
          ? [...selectedRowKeys, itemKey]
          : selectedRowKeys.filter((key) => key !== itemKey);

        // Map selected keys to their corresponding data items
        const newSelectedRows = newSelectedRowKeys
          .map((key) => keyToDataMap.get(key))
          .filter((row): row is T => row !== undefined);

        onChange(newSelectedRowKeys, newSelectedRows);
      },
      [selectedRowKeys, onChange, keyToDataMap],
    );

    // Enhanced render function that provides checkbox to user's renderItem
    const wrappedRenderItem = useCallback(
      (item: T, index: number) => {
        const itemKey = getItemKey(item, index);
        const isSelected = selectedKeysSet.has(itemKey);
        const checkboxProps = getCheckboxProps?.(item) || {};

        const checkbox = (
          <Checkbox
            checked={isSelected}
            onChange={(e) => handleCheckboxChange(itemKey, e.target.checked)}
            {...checkboxProps}
            aria-label={`Select item ${itemKey}`}
          />
        );

        return renderItem(item, index, checkbox);
      },
      [renderItem, selectedKeysSet, getCheckboxProps, handleCheckboxChange],
    );

    return (
      <WrappedComponent
        {...props}
        dataSource={dataSource}
        renderItem={wrappedRenderItem}
      />
    );
  };

  WrappedList.displayName = "CustomList";
  return WrappedList;
};

/**
 * Enhanced List component that adds row selection functionality to Ant Design's Table.
 * It adds a checkbox param to the renderItem so you can render it (usually in the avatar position).
 * For an example, check out the CustomList POC in the admin-ui repo.
 */
const CustomListComponent = withCustomProps(List);

// Attach List subcomponents to maintain API compatibility with Ant Design List
type CustomListType = typeof CustomListComponent & {
  Item: typeof List.Item;
};

export const CustomList = CustomListComponent as CustomListType;
CustomList.Item = List.Item;
