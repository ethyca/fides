import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntFlex as Flex,
  AntList as List,
  AntPopover as Popover,
  AntSpace as Space,
} from "fidesui";
import { useCallback } from "react";

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
    resetToDefault,
    applyFilters,

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

  const filterContent = (
    <div className="min-w-[220px] p-2">
      <div className="flex flex-col gap-1.5 mb-[14px]">
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
      </div>
      <Flex justify="space-between">
        <Button size="small" onClick={resetToDefault}>
          Reset
        </Button>
        <Button size="small" type="primary" onClick={applyFilters}>
          Apply
        </Button>
      </Flex>
    </div>
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
        >
          <Button className="flex items-center gap-2">Filter</Button>
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
