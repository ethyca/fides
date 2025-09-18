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
  const [statusFilters, setStatusFilters] = useState<string[]>(["pending", "in_processing", "paused", "retrying", "error"]); // Default to all "in progress" states plus error tasks
  const [showDismissed, setShowDismissed] = useState(false); // Default to not showing dismissed tasks

  const updateSearch = useCallback((newSearch: string) => {
    setSearchQuery(newSearch);
    setPageIndex(1); // Reset to first page when searching
  }, []);

  const updateStatusFilters = useCallback((filters: string[]) => {
    setStatusFilters(filters);
    setPageIndex(1);
  }, []);

  const updateShowDismissed = useCallback((show: boolean) => {
    setShowDismissed(show);
    setPageIndex(1);
  }, []);

  // Default button: Reset to all "In Progress" states plus error tasks (pending, in_processing, paused, retrying, error)
  const resetToDefault = useCallback(() => {
    setStatusFilters(["pending", "in_processing", "paused", "retrying", "error"]);
    setShowDismissed(false);
    setPageIndex(1);
  }, []);

  // Clear button: Remove all filters
  const clearAllFilters = useCallback(() => {
    setStatusFilters([]);
    setShowDismissed(true); // When clearing all filters, show everything including dismissed
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
    statuses: statusFilters.length > 0 ? statusFilters : undefined,
    return_dismissed: showDismissed,
  });

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
  };
};
