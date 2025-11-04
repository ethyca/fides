import { Checkbox, List, ListProps } from "antd/lib";
import type { ListItemProps } from "antd/lib/list";
import React, { useCallback, useEffect, useId, useMemo } from "react";

import { useListHotkeys } from "../hooks/useListHotkeys";
import styles from "./CustomList.module.scss";

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
    isActive?: boolean,
  ) => React.ReactNode;
  /** Whether to enable keyboard shortcuts for navigation and selection.
   * Never enable this on more than one list on the same page or these will conflict.
   * Defaults to false. */
  enableKeyboardShortcuts?: boolean;
  /** Callback that fires when the focused item index changes.
   * Receives the active item data and the new active index (or null if no item is active). */
  onActiveItemChange?: (
    activeListItem: T | null,
    activeListItemIndex?: number | null,
  ) => void;
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
    enableKeyboardShortcuts = false,
    onActiveItemChange,
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
    const { activeListItemIndex } = useListHotkeys({
      itemCount: dataSource?.length ?? 0,
      selectedKeys: selectedRowKeys,
      onToggleSelection: rowSelection ? handleKeyboardToggle : undefined,
      getItemKey: (index) =>
        dataSource ? getItemKey(dataSource[index], index) : index,
      listId,
      enabled: enableKeyboardShortcuts,
    });

    // Call onFocusChange callback when focused item changes
    useEffect(() => {
      if (onActiveItemChange && dataSource) {
        const activeListItem =
          activeListItemIndex !== null ? dataSource[activeListItemIndex] : null;
        onActiveItemChange(activeListItem, activeListItemIndex);
      }
    }, [activeListItemIndex, dataSource, onActiveItemChange]);

    // Helper function to apply focus styling and data attributes
    const applyActiveStyling = useCallback(
      (renderedItem: React.ReactNode, index: number, isActive: boolean) => {
        if (React.isValidElement(renderedItem)) {
          const itemProps = renderedItem.props as ListItemProps;
          return React.cloneElement(renderedItem, {
            ...itemProps,
            "data-listitem": `${listId}-${index}`,
            "aria-current": isActive ? "true" : undefined,
            className: isActive
              ? `${itemProps.className ?? ""} ${styles["active-item"]}`.trim()
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
          const isActive = activeListItemIndex === index;
          const renderedItem = renderItem(item, index, undefined, isActive);
          return applyActiveStyling(renderedItem, index, isActive);
        },
        [renderItem, activeListItemIndex, applyActiveStyling],
      );

      return (
        <WrappedComponent
          {...props}
          dataSource={dataSource}
          renderItem={basicRenderItem}
        />
      );
    }

    // Enhanced render function that provides checkbox and active state to user's renderItem
    const wrappedRenderItem = useCallback(
      (item: T, index: number) => {
        const itemKey = getItemKey(item, index);
        const isSelected = selectedKeysSet.has(itemKey);
        const isActive = activeListItemIndex === index;
        const checkboxProps = getCheckboxProps?.(item) || {};

        const checkbox = (
          <Checkbox
            checked={isSelected}
            onChange={(e) => handleCheckboxChange(itemKey, e.target.checked)}
            {...checkboxProps}
            aria-label={`Select item ${itemKey}`}
            className={enableKeyboardShortcuts ? "ml-2" : undefined} // active rows need a bit of padding to the left or it will be too close to edge
          />
        );

        const renderedItem = renderItem(item, index, checkbox, isActive);
        return applyActiveStyling(renderedItem, index, isActive);
      },
      [
        renderItem,
        selectedKeysSet,
        getCheckboxProps,
        handleCheckboxChange,
        activeListItemIndex,
        applyActiveStyling,
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
 * - Keyboard navigation: j (down), k (up), space (toggle selection), escape (clear active)
 * - Automatic scroll-into-view for active items (uses data-listitem attribute)
 * - Automatic active item styling with `var(--ant-color-primary-bg)` background color
 * - Active state provided to renderItem for additional custom styling
 * - Optional item selection with checkboxes
 * - onActiveItemChange callback to track currently active item
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
 * // List with custom active item styling (in addition to automatic background)
 * <CustomList
 *   dataSource={items}
 *   renderItem={(item, index, checkbox, isActive) => (
 *     <List.Item className={isActive ? 'custom-active-class' : ''}>
 *       {item.title}
 *     </List.Item>
 *   )}
 * />
 *
 * @example
 * // List with item selection and keyboard navigation
 * <CustomList
 *   dataSource={items}
 *   itemSelection={{
 *     selectedItemKeys: selected,
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
