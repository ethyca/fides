import { Checkbox, CheckboxProps, List, ListProps } from "antd/lib";
import type { ListItemProps } from "antd/lib/list";
import React, { useCallback, useId, useMemo } from "react";

import { useListKeyboardNavigation } from "../hooks/useListKeyboardNavigation";
import styles from "./CustomList.module.scss";

export interface RowSelection<T> {
  selectedRowKeys?: React.Key[];
  onChange?: (selectedRowKeys: React.Key[], selectedRows: T[]) => void;
  getCheckboxProps?: (record: T) => CheckboxProps;
}

export interface CustomListProps<T> extends Omit<ListProps<T>, "renderItem"> {
  rowSelection?: RowSelection<T>;
  renderItem?: (
    item: T,
    index: number,
    checkbox?: React.ReactNode,
    focused?: boolean,
  ) => React.ReactNode;
  /** Whether to enable keyboard shortcuts for navigation and selection.
   * Never enable this on more than one list on the same page or these will conflict.
   * Defaults to false. */
  enableKeyboardShortcuts?: boolean;
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
    enableKeyboardShortcuts,
    ...props
  }: CustomListProps<T>) => {
    // Generate a unique ID for this list instance
    const listId = useId();

    const selectedRowKeys = rowSelection?.selectedRowKeys ?? [];
    const onChange = rowSelection?.onChange;
    const getCheckboxProps = rowSelection?.getCheckboxProps;

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

    // Wrapper for keyboard toggle that checks disabled state
    const handleKeyboardToggle = useCallback(
      (itemKey: React.Key, checked: boolean) => {
        if (!dataSource || !getCheckboxProps) {
          handleCheckboxChange(itemKey, checked);
          return;
        }

        // Find the item and check if it's disabled
        const index = dataSource.findIndex(
          (item, idx) => getItemKey(item, idx) === itemKey,
        );
        if (index !== -1) {
          const item = dataSource[index];
          const checkboxProps = getCheckboxProps(item);
          if (!checkboxProps?.disabled) {
            handleCheckboxChange(itemKey, checked);
          }
        }
      },
      [dataSource, getCheckboxProps, handleCheckboxChange],
    );

    // Keyboard navigation hook - always enabled, works with or without rowSelection
    const { focusedItemIndex } = useListKeyboardNavigation({
      itemCount: dataSource?.length ?? 0,
      selectedKeys: selectedRowKeys,
      onToggleSelection: rowSelection ? handleKeyboardToggle : undefined,
      getItemKey: (index) =>
        dataSource ? getItemKey(dataSource[index], index) : index,
      listId,
      enabled: enableKeyboardShortcuts,
    });

    // Helper function to apply focus styling and data attributes
    const applyFocusStyling = useCallback(
      (renderedItem: React.ReactNode, index: number, isFocused: boolean) => {
        if (React.isValidElement(renderedItem)) {
          const itemProps = renderedItem.props as ListItemProps;
          return React.cloneElement(renderedItem, {
            ...itemProps,
            "data-listitem": `${listId}-${index}`,
            "aria-current": isFocused ? "true" : undefined,
            className: isFocused
              ? `${itemProps.className ?? ""} ${styles["pseudo-focus"]}`.trim()
              : itemProps.className,
          } as ListItemProps);
        }
        return renderedItem;
      },
      [listId],
    );

    // If no renderItem provided, render basic list
    if (!renderItem) {
      return <WrappedComponent {...props} dataSource={dataSource} />;
    }

    // If no rowSelection, provide renderItem with just focus state
    if (!rowSelection) {
      const basicRenderItem = useCallback(
        (item: T, index: number) => {
          const isFocused = focusedItemIndex === index;
          const renderedItem = renderItem(item, index, undefined, isFocused);
          return applyFocusStyling(renderedItem, index, isFocused);
        },
        [renderItem, focusedItemIndex, applyFocusStyling],
      );

      return (
        <WrappedComponent
          {...props}
          dataSource={dataSource}
          renderItem={basicRenderItem}
        />
      );
    }

    // Enhanced render function that provides checkbox and focus state to user's renderItem
    const wrappedRenderItem = useCallback(
      (item: T, index: number) => {
        const itemKey = getItemKey(item, index);
        const isSelected = selectedKeysSet.has(itemKey);
        const isFocused = focusedItemIndex === index;
        const checkboxProps = getCheckboxProps?.(item) || {};

        const checkbox = (
          <Checkbox
            checked={isSelected}
            onChange={(e) => handleCheckboxChange(itemKey, e.target.checked)}
            aria-label={checkboxProps.title ?? `Select item ${itemKey}`}
            {...checkboxProps}
            className={enableKeyboardShortcuts ? "ml-2" : undefined} // focused rows need a bit of padding to the left or it will be too close to edge
          />
        );

        const renderedItem = renderItem(item, index, checkbox, isFocused);
        return applyFocusStyling(renderedItem, index, isFocused);
      },
      [
        renderItem,
        selectedKeysSet,
        getCheckboxProps,
        handleCheckboxChange,
        focusedItemIndex,
        applyFocusStyling,
        enableKeyboardShortcuts,
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
 * Enhanced List component that adds row selection and keyboard navigation to Ant Design's List.
 *
 * Features:
 * - Keyboard navigation: j (down), k (up), space (toggle selection), escape (clear focus)
 * - Automatic scroll-into-view for focused items (uses data-listitem attribute)
 * - Automatic focus styling with `var(--ant-color-primary-bg)` background color
 * - Focus state provided to renderItem for additional custom styling
 * - Optional row selection with checkboxes
 *
 * Everything is automatic - keyboard shortcuts, scroll, styling, and data attributes
 * are all handled internally. Just provide your data and renderItem!
 *
 * Set enableKeyboardShortcuts = false to disable keyboard navigation.
 *
 * @example
 * // Basic list with keyboard navigation (everything automatic!)
 * <CustomList
 *   dataSource={items}
 *   renderItem={(item) => (
 *     <List.Item>{item.title}</List.Item>
 *   )}
 * />
 *
 * @example
 * // List with custom focus styling (in addition to automatic background)
 * <CustomList
 *   dataSource={items}
 *   renderItem={(item, index, checkbox, focused) => (
 *     <List.Item className={focused ? 'custom-focus-class' : ''}>
 *       {item.title}
 *     </List.Item>
 *   )}
 * />
 *
 * @example
 * // List with row selection and keyboard navigation
 * <CustomList
 *   dataSource={items}
 *   rowSelection={{
 *     selectedRowKeys: selected,
 *     onChange: handleChange,
 *   }}
 *   renderItem={(item, index, checkbox) => (
 *     <List.Item>
 *       <List.Item.Meta avatar={checkbox} title={item.title} />
 *     </List.Item>
 *   )}
 * />
 *
 * @example
 * // Disable keyboard shortcuts
 * <CustomList
 *   dataSource={items}
 *   enableKeyboardShortcuts={false}
 *   renderItem={(item) => <List.Item>{item.title}</List.Item>}
 * />
 *
 * For more examples, check out the CustomList POC in the admin-ui repo.
 */
const CustomListComponent = withCustomProps(List);

// Attach List subcomponents to maintain API compatibility with Ant Design List
type CustomListType = typeof CustomListComponent & {
  Item: typeof List.Item;
};

export const CustomList = CustomListComponent as CustomListType;
CustomList.Item = List.Item;
