import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntFlex as Flex,
  AntList as List,
  AntPopover as Popover,
  AntSelect as Select,
  AntSpace as Space,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import { useState } from "react";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import { MonitorTaskInProgressResponse } from "~/types/api";

import { useInProgressMonitorTasksList } from "../hooks/useInProgressMonitorTasksList";
import { InProgressMonitorTaskItem } from "./InProgressMonitorTaskItem";

const { Text } = Typography;

// Helper function to format status names for display
const formatStatusForDisplay = (status: string): string => {
  // Special case: "paused" should display as "Awaiting Processing"
  if (status === "paused") {
    return "Awaiting Processing";
  }

  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

interface InProgressMonitorTasksListProps {
  monitorId?: string;
}

export const InProgressMonitorTasksList = ({
  monitorId,
}: InProgressMonitorTasksListProps) => {
  const [showFilters, setShowFilters] = useState(false);

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

    // Loading states
    isLoading,
    isFetching,
  } = useInProgressMonitorTasksList({ monitorId });

  // Count active filters (status filters + whether dismissed is shown)
  const activeFilterCount = statusFilters.length + (showDismissed ? 1 : 0);

  const filterContent = (
    <div style={{ padding: "8px", minWidth: "200px" }}>
      <Select
        mode="multiple"
        placeholder="Select status..."
        value={statusFilters}
        onChange={updateStatusFilters}
        style={{ width: "100%", marginBottom: "12px" }}
        options={availableStatuses.map(status => ({
          label: formatStatusForDisplay(status),
          value: status,
        }))}
        allowClear
      />
      <Checkbox
        checked={showDismissed}
        onChange={(e) => updateShowDismissed(e.target.checked)}
        style={{ marginBottom: "12px" }}
      >
        Show dismissed tasks
      </Checkbox>
      <div>
        <Space>
          <Button size="small" onClick={resetToDefault}>
            Default
          </Button>
          <Button size="small" onClick={clearAllFilters}>
            Clear
          </Button>
        </Space>
      </div>
    </div>
  );

  return (
    <>
      {/* Search Row */}
      <Flex justify="space-between" align="center" style={{ marginBottom: "16px" }}>
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          placeholder="Search by monitor name..."
          style={{ minWidth: "300px" }}
        />

        {/* Filter Popover */}
        <Popover
          content={filterContent}
          trigger="click"
          placement="bottomRight"
          open={showFilters}
          onOpenChange={setShowFilters}
        >
          <Button style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span>Filter</span>
              {activeFilterCount > 0 && (
                <span style={{
                  background: "#1890ff",
                  color: "white",
                  borderRadius: "10px",
                  padding: "2px 6px",
                  fontSize: "10px",
                  minWidth: "16px",
                  textAlign: "center",
                  lineHeight: "1",
                  fontWeight: "600"
                }}>
                  {activeFilterCount}
                </span>
              )}
            </span>
            {showFilters ? <Icons.ChevronDown /> : <Icons.ChevronRight />}
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
