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

  const updateSearch = useCallback((newSearch: string) => {
    setSearchQuery(newSearch);
    setPageIndex(1); // Reset to first page when searching
  }, []);

  const { data, isLoading, isFetching } = useGetInProgressMonitorTasksQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    show_completed: showCompleted,
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

    // Ant Design list integration
    listProps,

    // Loading states
    isLoading,
    isFetching,
  };
};
