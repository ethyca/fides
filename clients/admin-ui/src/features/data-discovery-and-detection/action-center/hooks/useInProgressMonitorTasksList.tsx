import { AntEmpty as Empty } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { MonitorTaskInProgressResponse } from "~/types/api";

import { useGetInProgressMonitorTasksQuery } from "../action-center.slice";

interface UseInProgressMonitorTasksListConfig {
  monitorId?: string; // Optional since this shows tasks from all monitors
}

export const useInProgressMonitorTasksList = ({
  monitorId,
}: UseInProgressMonitorTasksListConfig = {}) => {
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState("");
  const [connectionNameFilters, setConnectionNameFilters] = useState<string[]>([]);
  const [taskTypeFilters, setTaskTypeFilters] = useState<string[]>([]);
  const [statusFilters, setStatusFilters] = useState<string[]>(["pending", "in_processing", "paused", "retrying"]); // Default to all "in progress" states (active, waiting, retrying)

  const updateSearch = useCallback((newSearch: string) => {
    setSearchQuery(newSearch);
    setPageIndex(1); // Reset to first page when searching
  }, []);

  const updateConnectionNameFilters = useCallback((filters: string[]) => {
    setConnectionNameFilters(filters);
    setPageIndex(1);
  }, []);

  const updateTaskTypeFilters = useCallback((filters: string[]) => {
    setTaskTypeFilters(filters);
    setPageIndex(1);
  }, []);

  const updateStatusFilters = useCallback((filters: string[]) => {
    setStatusFilters(filters);
    setPageIndex(1);
  }, []);

  // Default button: Reset to all "In Progress" states (pending, in_processing, paused, retrying)
  const resetToDefault = useCallback(() => {
    setConnectionNameFilters([]);
    setTaskTypeFilters([]);
    setStatusFilters(["pending", "in_processing", "paused", "retrying"]);
    setPageIndex(1);
  }, []);

  // Clear button: Remove all filters
  const clearAllFilters = useCallback(() => {
    setConnectionNameFilters([]);
    setTaskTypeFilters([]);
    setStatusFilters([]);
    setPageIndex(1);
  }, []);

  // All possible status values from ExecutionLogStatus enum
  // Note: awaiting_processing displays as "Awaiting Processing" but maps to "paused" in the API
  const allPossibleStatuses = [
    "pending",
    "in_processing",
    "complete",
    "error",
    "paused", // This is the actual enum value for "awaiting_processing"
    "retrying",
    "skipped"
  ];

  const { data, isLoading, isFetching } = useGetInProgressMonitorTasksQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    connection_names: connectionNameFilters.length > 0 ? connectionNameFilters : undefined,
    task_types: taskTypeFilters.length > 0 ? taskTypeFilters : undefined,
    statuses: statusFilters.length > 0 ? statusFilters : undefined,
  });

  // Extract unique values for filter options
  const availableConnectionNames = useMemo(() => {
    const names = new Set<string>();
    data?.items?.forEach(item => {
      if (item.connection_name) {
        names.add(item.connection_name);
      }
    });
    return Array.from(names).sort();
  }, [data?.items]);

  const availableTaskTypes = useMemo(() => {
    const types = new Set<string>();
    data?.items?.forEach(item => {
      if (item.action_type) {
        types.add(item.action_type);
      }
    });
    return Array.from(types).sort();
  }, [data?.items]);

  // Use all possible statuses instead of just what's in current data
  const availableStatuses = allPossibleStatuses;

  const listProps = useMemo(
    () => ({
      dataSource: data?.items || [],
      loading: isLoading || isFetching,
      locale: {
        emptyText: (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No tasks in progress"
          />
        ),
      },
      pagination: {
        current: pageIndex,
        pageSize,
        total: data?.total || 0,
        showSizeChanger: false,
        showQuickJumper: false,
        onChange: (page: number) => setPageIndex(page),
      },
    }),
    [data?.items, data?.total, isLoading, isFetching, pageIndex, pageSize],
  );

  return {
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
  };
};
