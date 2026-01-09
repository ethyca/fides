import { Empty } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { useSearch } from "~/features/common/hooks";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { ExecutionLogStatus } from "~/types/api/models/ExecutionLogStatus";

import { useGetInProgressMonitorTasksQuery } from "../action-center.slice";

export const useInProgressMonitorTasksList = () => {
  const { resetPagination, pageIndex, pageSize, paginationProps } =
    useAntPagination();

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
      resetPagination();
    },
    [setSearchQuery, resetPagination],
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
    resetPagination();
  }, [stagedStatusFilters, stagedShowDismissed, resetPagination]);

  // Reset button: Reset to defaults and immediately apply them
  const resetAndApplyFilters = useCallback(() => {
    setStagedStatusFilters(defaultStatusFilters);
    setStagedShowDismissed(false);
    setAppliedStatusFilters(defaultStatusFilters);
    setAppliedShowDismissed(false);
    resetPagination();
  }, [defaultStatusFilters, resetPagination]);

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

  const { data, isLoading, isFetching } = useGetInProgressMonitorTasksQuery(
    {
      page: pageIndex,
      size: pageSize,
      search: searchQuery,
      statuses:
        appliedStatusFilters.length > 0 ? appliedStatusFilters : undefined,
      return_dismissed: appliedShowDismissed,
    },
    {
      pollingInterval: 3000,
      refetchOnFocus: true,
      refetchOnReconnect: true,
    },
  );

  const listProps = useMemo(
    () => ({
      dataSource: data?.items || [],
      loading: isLoading,
      locale: {
        emptyText: (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="No tasks in progress"
          />
        ),
      },
    }),
    [data?.items, isLoading],
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

    paginationProps: {
      ...paginationProps,
      total: data?.total,
    },

    // Loading states
    isLoading,
    isFetching,
  };
};
