import { ChevronDown } from "@carbon/icons-react";
import type { PopoverProps, TreeProps } from "antd/lib";
import { Button, Divider, Flex, Input, Popover, Space, Tree } from "antd/lib";
import _ from "lodash";
import { useEffect, useState } from "react";

import { filterTreeData, getAllTreeKeys } from "./filter.utils";

export interface FilterProps {
  treeProps: TreeProps;
  onApply?: () => void;
  onReset?: () => void;
  onClear?: () => void;
  activeFiltersCount?: number;
  popoverProps?: Omit<PopoverProps, "content">;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  showSearch?: boolean;
}

/**
 * Filter component that combines Popover, Search, and Tree for filtering data.
 * The button label updates to show the count of active filters.
 *
 * @param treeProps - Ant Design Tree props for the tree component
 * @param onApply - Callback when Apply button is clicked
 * @param onReset - Callback when Reset button is clicked
 * @param onClear - Callback when Clear button is clicked
 * @param activeFiltersCount - Number of active filters to display in button label (shows "Filter (n)")
 * @param popoverProps - Ant Design Popover props to extend the popover
 * @param open - Whether the popover is open (controlled mode)
 * @param onOpenChange - Callback when the popover open state changes
 * @param showSearch - Whether to show the search input (defaults to true)
 *
 * @example
 * ```tsx
 * <Filter
 *   activeFiltersCount={5}
 *   showSearch={true}
 *   treeProps={{
 *     checkable: true,
 *     checkedKeys: checkedKeys,
 *     onCheck: (checked) => setCheckedKeys(checked),
 *     treeData: myTreeData,
 *   }}
 *   onApply={() => console.log('Apply filters')}
 *   onReset={() => setCheckedKeys([])}
 *   onClear={() => setCheckedKeys([])}
 * />
 * ```
 */
export const Filter = ({
  treeProps,
  onApply,
  onReset,
  onClear,
  activeFiltersCount = 0,
  popoverProps,
  open,
  onOpenChange,
  showSearch = true,
}: FilterProps) => {
  const [internalOpen, setInternalOpen] = useState(false);
  const [searchValue, setSearchValue] = useState("");
  const [internalChecked, setInternalChecked] = useState(
    Array.isArray(treeProps.checkedKeys)
      ? treeProps.checkedKeys
      : treeProps?.checkedKeys?.checked,
  );

  const isControlled = open !== undefined;
  const isOpen = isControlled ? open : internalOpen;

  const handleOpenChange = (newOpen: boolean) => {
    if (!isControlled) {
      setInternalOpen(newOpen);
    }
    onOpenChange?.(newOpen);
  };

  const handleApply = () => {
    onApply?.();
    handleOpenChange(false);
  };

  const handleReset = () => {
    onReset?.();
    setSearchValue("");
  };

  const handleClear = () => {
    onClear?.();
    setSearchValue("");
  };

  const filteredData = showSearch
    ? filterTreeData(searchValue, treeProps.treeData)
    : treeProps.treeData;

  // Augmenting onCheck event to include checked values hidden by search filter
  const handleOnCheck: TreeProps["onCheck"] = (checked, info) => {
    const checkedKeysArray = Array.isArray(checked) ? checked : checked.checked;
    const hiddenKeys = _.without(
      getAllTreeKeys(treeProps.treeData),
      ...getAllTreeKeys(filteredData),
    );

    const unfilteredChecked = [
      ..._.intersection(hiddenKeys, internalChecked),
      ...checkedKeysArray,
    ];

    setInternalChecked(unfilteredChecked);
    treeProps.onCheck?.(unfilteredChecked, info);
  };

  const expandedKeys =
    showSearch && searchValue
      ? getAllTreeKeys(filteredData)
      : treeProps.expandedKeys;

  // Syncing externally controlled state
  useEffect(() => {
    const checkedKeysArray = Array.isArray(treeProps.checkedKeys)
      ? treeProps.checkedKeys
      : treeProps?.checkedKeys?.checked;

    setInternalChecked(checkedKeysArray);
  }, [treeProps.checkedKeys]);

  const content = (
    <Flex vertical gap="small" className="py-2 min-w-72">
      {showSearch && (
        <Flex className="px-2">
          <Input
            placeholder="Search filters"
            aria-label="Search filters"
            value={searchValue}
            onChange={(e) => setSearchValue(e.target.value)}
            allowClear
            className="w-full"
            size="small"
          />
        </Flex>
      )}

      <Flex className="max-h-72 overflow-y-auto px-2">
        <Tree
          {...treeProps}
          onCheck={handleOnCheck}
          treeData={filteredData}
          expandedKeys={expandedKeys}
        />
      </Flex>

      <Divider className="my-0" />
      <Flex justify="space-between" align="center" className="px-2">
        <Button
          type="text"
          size="small"
          onClick={handleClear}
          style={{ color: "var(--ant-color-text-secondary)" }}
        >
          Clear
        </Button>
        <Space>
          <Button size="small" onClick={handleReset}>
            Reset
          </Button>
          <Button size="small" type="primary" onClick={handleApply}>
            Apply
          </Button>
        </Space>
      </Flex>
    </Flex>
  );

  const buttonLabel =
    activeFiltersCount > 0 ? `Filter (${activeFiltersCount})` : "Filter";

  return (
    <Popover
      content={content}
      trigger="click"
      open={isOpen}
      onOpenChange={handleOpenChange}
      placement="bottomRight"
      {...popoverProps}
    >
      <Button
        icon={activeFiltersCount > 0 ? undefined : <ChevronDown />}
        iconPosition="end"
        aria-label={
          activeFiltersCount > 0
            ? `Filter, ${activeFiltersCount} active`
            : "Filter"
        }
      >
        {buttonLabel}
      </Button>
    </Popover>
  );
};

export default Filter;
