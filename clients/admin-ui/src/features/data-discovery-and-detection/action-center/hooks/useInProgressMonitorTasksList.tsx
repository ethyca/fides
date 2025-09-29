import { AntEmpty as Empty } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { usePagination, useSearch } from "~/features/common/hooks";
import { ExecutionLogStatus } from "~/types/api/models/ExecutionLogStatus";

import { useGetInProgressMonitorTasksQuery } from "../action-center.slice";

export const useInProgressMonitorTasksList = () => {
  const {
    pageIndex,
    pageSize,
    updatePageIndex,
    resetPagination,
    showSizeChanger,
  } = usePagination({ defaultPageSize: 20, showSizeChanger: false });

  const { searchQuery, updateSearch: setSearchQuery } = useSearch();

  const [statusFilters, setStatusFilters] = useState<ExecutionLogStatus[]>([
    ExecutionLogStatus.PENDING,
    ExecutionLogStatus.IN_PROCESSING,
    ExecutionLogStatus.PAUSED,
    ExecutionLogStatus.RETRYING,
    ExecutionLogStatus.ERROR,
  ]); // Default to all "in progress" states plus error tasks
  const [showDismissed, setShowDismissed] = useState(false); // Default to not showing dismissed tasks

  const updateSearch = useCallback(
    (newSearch: string) => {
      setSearchQuery(newSearch);
      updatePageIndex(1); // Reset to first page when searching
    },
    [setSearchQuery, updatePageIndex],
  );

  const updateStatusFilters = useCallback(
    (filters: ExecutionLogStatus[]) => {
      setStatusFilters(filters);
      updatePageIndex(1);
    },
    [updatePageIndex],
  );

  const updateShowDismissed = useCallback(
    (show: boolean) => {
      setShowDismissed(show);
      updatePageIndex(1);
    },
    [updatePageIndex],
  );

  // Default button: Reset to all "In Progress" states plus error tasks (pending, in_processing, paused, retrying, error)
  const resetToDefault = useCallback(() => {
    setStatusFilters([
      ExecutionLogStatus.PENDING,
      ExecutionLogStatus.IN_PROCESSING,
      ExecutionLogStatus.PAUSED,
      ExecutionLogStatus.RETRYING,
      ExecutionLogStatus.ERROR,
    ]);
    setShowDismissed(false);
    resetPagination();
  }, [resetPagination]);

  // Clear button: Remove all filters
  const clearAllFilters = useCallback(() => {
    setStatusFilters([]);
    setShowDismissed(true); // When clearing all filters, show everything including dismissed
    resetPagination();
  }, [resetPagination]);

  // All possible status values from ExecutionLogStatus enum
  // Note: awaiting_processing displays as "Awaiting Processing" but maps to "paused" in the API
  const allPossibleStatuses: ExecutionLogStatus[] = [
    ExecutionLogStatus.PENDING,
    ExecutionLogStatus.IN_PROCESSING,
    ExecutionLogStatus.COMPLETE,
    ExecutionLogStatus.ERROR,
    ExecutionLogStatus.PAUSED, // This is the actual enum value for "awaiting_processing"
    ExecutionLogStatus.RETRYING,
    ExecutionLogStatus.SKIPPED,
  ];

  const { data, isLoading, isFetching } = useGetInProgressMonitorTasksQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    statuses: statusFilters.length > 0 ? statusFilters : undefined,
    return_dismissed: showDismissed,
  });

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
        showSizeChanger,
        showQuickJumper: false,
        onChange: (page: number) => updatePageIndex(page),
      },
    }),
    [
      data?.items,
      data?.total,
      isLoading,
      isFetching,
      pageIndex,
      pageSize,
      showSizeChanger,
      updatePageIndex,
    ],
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
    availableStatuses: allPossibleStatuses,

    // Ant Design list integration
    listProps,

    // Loading states
    isLoading,
    isFetching,
  };
};
