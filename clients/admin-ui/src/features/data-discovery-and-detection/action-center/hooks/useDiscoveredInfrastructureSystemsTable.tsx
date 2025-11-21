import { AntEmpty as Empty } from "fidesui";
import { useCallback, useMemo } from "react";

import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

import { useGetDiscoveredSystemAggregateQuery } from "../action-center.slice";
import { MONITOR_TYPES } from "../utils/getMonitorType";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "./useActionCenterTabs";
import { useDiscoveredInfrastructureSystemsColumns } from "./useDiscoveredInfrastructureSystemsColumns";

interface UseDiscoveredInfrastructureSystemsTableConfig {
  monitorId: string;
}

export const useDiscoveredInfrastructureSystemsTable = ({
  monitorId,
}: UseDiscoveredInfrastructureSystemsTableConfig) => {
  const { filterTabs, activeTab, onTabChange, activeParams } =
    useActionCenterTabs();

  const tableState = useTableState<"name">({
    sorting: {
      validColumns: ["name"],
    },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch, resetState } =
    tableState;

  const { data, isLoading, isFetching } = useGetDiscoveredSystemAggregateQuery({
    key: monitorId,
    page: pageIndex,
    size: pageSize,
    search: searchQuery,
    ...activeParams,
  });

  // Helper function to generate consistent row keys
  const getRecordKey = useCallback(
    (record: SystemStagedResourcesAggregateRecord) =>
      record.id ?? record.vendor_id ?? record.name ?? UNCATEGORIZED_SEGMENT,
    [],
  );

  const rowClickUrl = useCallback(
    (record: SystemStagedResourcesAggregateRecord) => {
      const newUrl = `${ACTION_CENTER_ROUTE}/${MONITOR_TYPES.INFRASTRUCTURE}/${monitorId}/${record.id ?? UNCATEGORIZED_SEGMENT}${activeTab ? `#${activeTab}` : ""}`;
      return newUrl;
    },
    [monitorId, activeTab],
  );

  const antTableConfig = useMemo(
    () => ({
      enableSelection: true,
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
              description="All caught up!"
            />
          ),
        },
      },
    }),
    [getRecordKey, isLoading, isFetching, data?.items, data?.total],
  );

  const antTable = useAntTable<SystemStagedResourcesAggregateRecord, "name">(
    tableState,
    antTableConfig,
  );

  const { selectedRows, resetSelections } = antTable;

  const handleTabChange = useCallback(
    async (tab: ActionCenterTabHash) => {
      await onTabChange(tab);
      resetState();
      resetSelections();
    },
    [onTabChange, resetState, resetSelections],
  );

  const { columns } = useDiscoveredInfrastructureSystemsColumns({
    rowClickUrl,
  });

  return {
    // Table state and data
    columns,
    data,
    isLoading,
    isFetching,
    searchQuery,
    updateSearch,
    resetState,

    // Ant Design table integration
    tableProps: antTable.tableProps,
    selectionProps: antTable.selectionProps,

    // Tab management
    filterTabs,
    activeTab,
    handleTabChange,
    activeParams,

    // Selection
    selectedRows,
    hasSelectedRows: antTable.hasSelectedRows,
    resetSelections,
  };
};
