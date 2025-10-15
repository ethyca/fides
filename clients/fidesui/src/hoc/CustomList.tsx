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

const withCustomProps = (WrappedComponent: typeof List) => {
  const WrappedList = <T,>({
    rowSelection,
    renderItem,
    dataSource,
    ...props
  }: CustomListProps<T>) => {
    // If no rowSelection, just render the original List
    if (!rowSelection || !renderItem) {
      return (
        <WrappedComponent
          {...props}
          dataSource={dataSource}
          renderItem={renderItem}
        />
      );
    }

    const { selectedRowKeys = [], onChange, getCheckboxProps } = rowSelection;

    // Create a map for quick lookup of selected keys
    const selectedKeysSet = useMemo(
      () => new Set(selectedRowKeys),
      [selectedRowKeys],
    );

    // Create a map of key to data for efficient lookup
    const keyToDataMap = useMemo(() => {
      const map = new Map<React.Key, T>();
      if (dataSource) {
        dataSource.forEach((item, index) => {
          // Extract the key from the item
          const key =
            (item as any).key !== undefined ? (item as any).key : index;
          map.set(key, item);
        });
      }
      return map;
    }, [dataSource]);

    // Handle checkbox selection
    const handleCheckboxChange = useCallback(
      (item: T, itemKey: React.Key, checked: boolean) => {
        if (!onChange) {
          return;
        }

        let newSelectedRowKeys: React.Key[];
        if (checked) {
          // Add to selection
          newSelectedRowKeys = [...selectedRowKeys, itemKey];
        } else {
          // Remove from selection
          newSelectedRowKeys = selectedRowKeys.filter((key) => key !== itemKey);
        }

        // Get the corresponding row data for all selected keys
        const newSelectedRows = newSelectedRowKeys
          .map((key) => keyToDataMap.get(key))
          .filter((row): row is T => row !== undefined);

        onChange(newSelectedRowKeys, newSelectedRows);
      },
      [selectedRowKeys, onChange, keyToDataMap],
    );

    // Wrapped render function that provides checkbox to user's renderItem
    const wrappedRenderItem = useCallback(
      (item: T, index: number) => {
        // Extract the key from the item (React List requires items to have keys)
        const itemKey =
          (item as any).key !== undefined ? (item as any).key : index;
        const isSelected = selectedKeysSet.has(itemKey);
        const checkboxProps = getCheckboxProps?.(item) || {};

        // Create the checkbox element if rowSelection is enabled
        const checkbox = rowSelection ? (
          <Checkbox
            checked={isSelected}
            onChange={(e) =>
              handleCheckboxChange(item, itemKey, e.target.checked)
            }
            {...checkboxProps}
            aria-label={`Select item ${itemKey}`}
          />
        ) : undefined;

        // Pass checkbox to user's renderItem function
        return renderItem(item, index, checkbox);
      },
      [
        renderItem,
        selectedKeysSet,
        getCheckboxProps,
        handleCheckboxChange,
        rowSelection,
      ],
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
 * Higher-order component that adds rowSelection functionality to Ant Design's List component.
 * Provides selection capability similar to Table's rowSelection, with checkboxes provided to renderItem.
 *
 * Default customizations:
 * - Provides checkbox as third parameter to renderItem when rowSelection is enabled
 * - Maintains selection state through selectedRowKeys
 * - Supports conditional disabling via getCheckboxProps
 * - Returns both selected keys and full row objects in onChange
 *
 * @example
 * ```tsx
 * // Basic usage with rowSelection
 * <CustomList
 *   dataSource={items}
 *   rowSelection={{
 *     selectedRowKeys: selected,
 *     onChange: (keys, rows) => setSelected(keys),
 *     getCheckboxProps: (item) => ({ disabled: item.locked })
 *   }}
 *   renderItem={(item, index, checkbox) => (
 *     <CustomList.Item>
 *       <Flex gap="middle" align="start">
 *         {checkbox}
 *         <CustomList.Item.Meta
 *           title={item.title}
 *           description={item.description}
 *         />
 *       </Flex>
 *     </CustomList.Item>
 *   )}
 * />
 *
 * // Without rowSelection (works like normal List, checkbox will be undefined)
 * <CustomList
 *   dataSource={items}
 *   renderItem={(item) => <CustomList.Item>{item.title}</CustomList.Item>}
 * />
 * ```
 */
const CustomListComponent = withCustomProps(List);

// Attach List subcomponents to maintain API compatibility with Ant Design List
type CustomListType = typeof CustomListComponent & {
  Item: typeof List.Item;
};

export const CustomList = CustomListComponent as CustomListType;
CustomList.Item = List.Item;
