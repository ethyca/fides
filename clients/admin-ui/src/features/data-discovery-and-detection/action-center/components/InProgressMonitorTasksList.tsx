import {
  AntButton as Button,
  AntFlex as Flex,
  AntList as List,
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
    connectionNameFilters,
    taskTypeFilters,
    statusFilters,
    updateConnectionNameFilters,
    updateTaskTypeFilters,
    updateStatusFilters,

    // Filter actions
    resetToDefault,
    clearAllFilters,

    // Available filter options
    availableConnectionNames,
    availableTaskTypes,
    availableStatuses,

    // Ant Design list integration
    listProps,

    // Loading states
    isLoading,
    isFetching,
  } = useInProgressMonitorTasksList({ monitorId });

  // Count active filters
  const activeFilterCount = connectionNameFilters.length + taskTypeFilters.length + statusFilters.length;

  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };

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

        {/* Filter Buttons */}
        <Space>
          <Button
            onClick={toggleFilters}
            style={{ display: "flex", alignItems: "center", gap: "6px" }}
          >
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

          <Button onClick={resetToDefault}>
            Default
          </Button>

          <Button onClick={clearAllFilters}>
            Clear
          </Button>
        </Space>
      </Flex>

      {/* Collapsible Filter Section */}
      {showFilters && (
        <div style={{
          background: "#fafafa",
          border: "1px solid #f0f0f0",
          borderRadius: "6px",
          padding: "16px",
          marginBottom: "16px"
        }}>
          <Flex gap={16} align="center" wrap="wrap">

            <Select
              mode="multiple"
              placeholder="Connection"
              value={connectionNameFilters}
              onChange={updateConnectionNameFilters}
              style={{ minWidth: "150px" }}
              options={availableConnectionNames.map(name => ({
                label: name,
                value: name,
              }))}
              allowClear
            />

            <Select
              mode="multiple"
              placeholder="Task Type"
              value={taskTypeFilters}
              onChange={updateTaskTypeFilters}
              style={{ minWidth: "150px" }}
              options={availableTaskTypes.map(type => ({
                label: type.charAt(0).toUpperCase() + type.slice(1),
                value: type,
              }))}
              allowClear
            />

            <Select
              mode="multiple"
              placeholder="Status"
              value={statusFilters}
              onChange={updateStatusFilters}
              style={{ minWidth: "150px" }}
              options={availableStatuses.map(status => ({
                label: formatStatusForDisplay(status),
                value: status,
              }))}
              allowClear
            />
          </Flex>
        </div>
      )}

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
