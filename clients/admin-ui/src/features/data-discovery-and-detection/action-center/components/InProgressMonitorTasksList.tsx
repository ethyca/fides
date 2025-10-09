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
    clearAllFilters,

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
    <div className="min-w-[220px] space-y-3 p-2">
      <Checkbox.Group
        value={statusFilters}
        onChange={handleStatusesChanged}
        className="flex flex-col gap-2"
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
        className="mb-2"
      >
        Show dismissed tasks
      </Checkbox>
      <Space>
        <Button size="small" onClick={resetToDefault}>
          Default
        </Button>
        <Button size="small" onClick={clearAllFilters}>
          Clear
        </Button>
      </Space>
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
        renderItem={(task) => (
          <List.Item>
            <InProgressMonitorTaskItem task={task} />
          </List.Item>
        )}
      />
    </>
  );
};
