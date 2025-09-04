import { AntEmpty as Empty } from "fidesui";
import { useCallback, useMemo } from "react";

import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { MonitorTaskInProgressResponse } from "~/types/api";

import { useGetInProgressMonitorTasksQuery } from "../action-center.slice";

interface UseInProgressMonitorTasksTableConfig {
  monitorId?: string; // Optional since this shows tasks from all monitors
}

export const useInProgressMonitorTasksTable = ({
  monitorId,
}: UseInProgressMonitorTasksTableConfig = {}) => {
  const tableState = useTableState({
    sorting: {
      validColumns: ["monitor_name", "task_type", "last_updated", "status"],
    },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch } = tableState;

  const { data, isLoading, isFetching } = useGetInProgressMonitorTasksQuery({
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
  });

  // Helper function to generate consistent row keys
  const getRecordKey = useCallback(
    (record: MonitorTaskInProgressResponse) => record.id,
    [],
  );

  const antTableConfig = useMemo(
    () => ({
      enableSelection: false, // No selection needed for in-progress tasks
      getRowKey: getRecordKey,
      isLoading,
      isFetching,
      dataSource: data?.items || [],
      totalRows: data?.total || 0,
      customTableProps: {
        locale: {
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="No tasks in progress"
            />
          ),
        },
      },
    }),
    [getRecordKey, isLoading, isFetching, data?.items, data?.total],
  );

  const antTable = useAntTable<MonitorTaskInProgressResponse, string>(
    tableState,
    antTableConfig,
  );

  const tableProps = antTable.getTableProps();

  return {
    // Table state and data
    searchQuery,
    updateSearch,

    // Ant Design table integration
    tableProps,

    // Loading states
    isLoading,
    isFetching,
  };
};
