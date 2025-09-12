import { AntEmpty as Empty } from "fidesui";
import { useCallback, useMemo, useState } from "react";

import { MonitorTaskInProgressResponse } from "~/types/api";

import { useGetInProgressMonitorTasksQuery } from "../action-center.slice";

interface UseInProgressMonitorTasksListConfig {
  monitorId?: string; // Optional since this shows tasks from all monitors
  showCompleted?: boolean;
}

export const useInProgressMonitorTasksList = ({
  monitorId,
  showCompleted = false,
}: UseInProgressMonitorTasksListConfig = {}) => {
  const [pageIndex, setPageIndex] = useState(1);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState("");
  const [connectionNameFilters, setConnectionNameFilters] = useState<string[]>([]);
  const [taskTypeFilters, setTaskTypeFilters] = useState<string[]>([]);
  const [statusFilters, setStatusFilters] = useState<string[]>([]);

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

  const { data, isLoading, isFetching } = useGetInProgressMonitorTasksQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    show_completed: showCompleted,
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

  const availableStatuses = useMemo(() => {
    const statuses = new Set<string>();
    data?.items?.forEach(item => {
      if (item.status) {
        statuses.add(item.status);
      }
    });
    return Array.from(statuses).sort();
  }, [data?.items]);

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
