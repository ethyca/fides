import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntDivider as Divider,
  AntFlex as Flex,
  AntList as List,
  AntPopover as Popover,
  Icons,
} from "fidesui";
import { useCallback, useState } from "react";

import { capitalize } from "~/features/common/utils";
import { MonitorTaskInProgressResponse } from "~/types/api";
import { ExecutionLogStatus } from "~/types/api/models/ExecutionLogStatus";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import { useInProgressMonitorTasksList } from "../hooks/useInProgressMonitorTasksList";
import { InProgressMonitorTaskItem } from "./InProgressMonitorTaskItem";

// Helper function to format status names for display
const formatStatusForDisplay = (
  status: ExecutionLogStatus | string,
): string => {
  // Special case: "paused" should display as "Awaiting Processing"
  if (status === "paused") {
    return "Awaiting Processing";
  }

  return status.split("_").map(capitalize).join(" ");
};

export const InProgressMonitorTasksList = () => {
  const [filterPopoverOpen, setFilterPopoverOpen] = useState(false);

  const {
    // List state and data
    searchQuery,
    updateSearch,

    // Filter states and controls
    statusFilters,
    updateStatusFilters,
    showDismissed,
    updateShowDismissed,

    // Filter actions
    applyFilters,
    resetAndApplyFilters,

    // Available filter options
    availableStatuses,

    // Ant Design list integration
    listProps,
  } = useInProgressMonitorTasksList();

  const handleStatusesChanged = useCallback(
    (values: Array<ExecutionLogStatus | string>) => {
      updateStatusFilters(values as ExecutionLogStatus[]);
    },
    [updateStatusFilters],
  );

  const handleApplyAndClose = useCallback(() => {
    applyFilters();
    setFilterPopoverOpen(false);
  }, [applyFilters]);

  const handleResetAndClose = useCallback(() => {
    resetAndApplyFilters();
    setFilterPopoverOpen(false);
  }, [resetAndApplyFilters]);

  const filterContent = (
    <Flex vertical className="min-w-[220px]">
      <Flex vertical className="gap-1.5 px-4 py-2">
        <Checkbox.Group
          value={statusFilters}
          onChange={handleStatusesChanged}
          className="flex flex-col gap-1.5"
        >
          {availableStatuses.map((status) => (
            <Checkbox key={status} value={status}>
              {formatStatusForDisplay(status)}
            </Checkbox>
          ))}
        </Checkbox.Group>
        <Checkbox
          checked={showDismissed}
          onChange={(e) => updateShowDismissed(e.target.checked)}
        >
          Dismissed
        </Checkbox>
      </Flex>
      <Divider className="m-0" />
      <Flex justify="space-between" className="px-4 py-2">
        <Button
          size="small"
          type="text"
          onClick={handleResetAndClose}
          className="-ml-2"
        >
          Reset
        </Button>
        <Button size="small" type="primary" onClick={handleApplyAndClose}>
          Apply
        </Button>
      </Flex>
    </Flex>
  );

  return (
    <>
      {/* Search Row */}
      <Flex justify="space-between" align="center" className="mb-4">
        <div className="min-w-[300px]">
          <DebouncedSearchInput
            value={searchQuery ?? ""}
            onChange={updateSearch}
            placeholder="Search by monitor name..."
          />
        </div>

        {/* Filter Popover */}
        <Popover
          content={filterContent}
          trigger="click"
          placement="bottomRight"
          open={filterPopoverOpen}
          onOpenChange={setFilterPopoverOpen}
        >
          <Button icon={<Icons.ChevronDown />} iconPosition="end">
            Filter
          </Button>
        </Popover>
      </Flex>

      <List
        {...listProps}
        renderItem={(task: MonitorTaskInProgressResponse) => (
          <List.Item>
            <InProgressMonitorTaskItem task={task} />
          </List.Item>
        )}
      />
    </>
  );
};
