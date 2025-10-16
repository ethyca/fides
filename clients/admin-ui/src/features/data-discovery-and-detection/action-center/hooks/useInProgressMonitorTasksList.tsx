import { AntEmpty as Empty } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { usePagination, useSearch } from "~/features/common/hooks";
import { ExecutionLogStatus } from "~/types/api/models/ExecutionLogStatus";

import { useGetInProgressMonitorTasksQuery } from "../action-center.slice";

export const useInProgressMonitorTasksList = () => {
  const { pageIndex, pageSize, updatePageIndex, showSizeChanger } =
    usePagination({ defaultPageSize: 20, showSizeChanger: false });

  const { searchQuery, updateSearch: setSearchQuery } = useSearch();

  const defaultStatusFilters = useMemo(
    () => [
      ExecutionLogStatus.PENDING,
      ExecutionLogStatus.IN_PROCESSING,
      ExecutionLogStatus.PAUSED,
      ExecutionLogStatus.RETRYING,
      ExecutionLogStatus.ERROR,
    ],
    [],
  );

  // Applied filters are what's actually used in the query
  const [appliedStatusFilters, setAppliedStatusFilters] =
    useState<ExecutionLogStatus[]>(defaultStatusFilters);
  const [appliedShowDismissed, setAppliedShowDismissed] = useState(false);

  // Staged filters are what the user is selecting in the UI
  const [stagedStatusFilters, setStagedStatusFilters] =
    useState<ExecutionLogStatus[]>(defaultStatusFilters);
  const [stagedShowDismissed, setStagedShowDismissed] = useState(false);

  const updateSearch = useCallback(
    (newSearch: string) => {
      setSearchQuery(newSearch);
      updatePageIndex(1); // Reset to first page when searching
    },
    [setSearchQuery, updatePageIndex],
  );

  const updateStatusFilters = useCallback((filters: ExecutionLogStatus[]) => {
    setStagedStatusFilters(filters);
  }, []);

  const updateShowDismissed = useCallback((show: boolean) => {
    setStagedShowDismissed(show);
  }, []);

  // Apply button: Apply staged filters to actual query
  const applyFilters = useCallback(() => {
    setAppliedStatusFilters(stagedStatusFilters);
    setAppliedShowDismissed(stagedShowDismissed);
    updatePageIndex(1);
  }, [stagedStatusFilters, stagedShowDismissed, updatePageIndex]);

  // Reset button: Reset to defaults and immediately apply them
  const resetAndApplyFilters = useCallback(() => {
    setStagedStatusFilters(defaultStatusFilters);
    setStagedShowDismissed(false);
    setAppliedStatusFilters(defaultStatusFilters);
    setAppliedShowDismissed(false);
    updatePageIndex(1);
  }, [defaultStatusFilters, updatePageIndex]);

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
    statuses:
      appliedStatusFilters.length > 0 ? appliedStatusFilters : undefined,
    return_dismissed: appliedShowDismissed,
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
        total: data?.total,
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

    // Filter states and controls (staged, not yet applied)
    statusFilters: stagedStatusFilters,
    updateStatusFilters,
    showDismissed: stagedShowDismissed,
    updateShowDismissed,

    // Filter actions
    applyFilters,
    resetAndApplyFilters,

    // Available filter options
    availableStatuses: allPossibleStatuses,

    // Ant Design list integration
    listProps,

    // Loading states
    isLoading,
    isFetching,
  };
};
