import { AntEmpty as Empty, useToast } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  ACTION_CENTER_ROUTE,
  SYSTEM_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { DiffStatus, SystemStagedResourcesAggregateRecord } from "~/types/api";

import {
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredSystemAggregateQuery,
  useIgnoreMonitorResultSystemsMutation,
} from "../action-center.slice";
import { SuccessToastContent } from "../SuccessToastContent";
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
  const router = useRouter();
  const toast = useToast();

  const { filterTabs, activeTab, onTabChange, activeParams, actionsDisabled } =
    useActionCenterTabs();

  const tableState = useTableState<"name" | "actions">({
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

  const [addMonitorResultSystemsMutation, { isLoading: isAddingResults }] =
    useAddMonitorResultSystemsMutation();
  const [ignoreMonitorResultSystemsMutation, { isLoading: isIgnoringResults }] =
    useIgnoreMonitorResultSystemsMutation();

  const anyBulkActionIsLoading = isAddingResults || isIgnoringResults;

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

  const antTable = useAntTable<
    SystemStagedResourcesAggregateRecord,
    "name" | "actions"
  >(tableState, antTableConfig);

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
    monitorId,
    onTabChange: handleTabChange,
    readonly: actionsDisabled,
    allowIgnore: !activeParams.diff_status.includes(DiffStatus.MUTED),
    rowClickUrl,
  });

  const handleBulkAdd = useCallback(async () => {
    const totalUpdates = selectedRows.reduce(
      (acc, row) => acc + row.total_updates!,
      0,
    );

    const result = await addMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: selectedRows.map((row) => row.id!),
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          SuccessToastContent(
            `${totalUpdates} assets have been added to the system inventory.`,
            () => router.push(SYSTEM_ROUTE),
          ),
        ),
      );
      resetSelections();
    }
  }, [
    selectedRows,
    addMonitorResultSystemsMutation,
    monitorId,
    toast,
    router,
    resetSelections,
  ]);

  const handleBulkIgnore = useCallback(async () => {
    const totalUpdates = selectedRows.reduce(
      (acc, row) => acc + row.total_updates!,
      0,
    );

    const result = await ignoreMonitorResultSystemsMutation({
      monitor_config_key: monitorId,
      resolved_system_ids: selectedRows.map(
        (row) => row.id ?? UNCATEGORIZED_SEGMENT,
      ),
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          SuccessToastContent(
            `${totalUpdates} assets have been ignored and will not appear in future scans.`,
            async () => {
              await onTabChange(ActionCenterTabHash.IGNORED);
            },
          ),
        ),
      );
      resetSelections();
    }
  }, [
    selectedRows,
    ignoreMonitorResultSystemsMutation,
    monitorId,
    toast,
    onTabChange,
    resetSelections,
  ]);

  const uncategorizedIsSelected = selectedRows.some((row) => row.id === null);

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
    actionsDisabled,

    // Selection
    selectedRows,
    hasSelectedRows: antTable.hasSelectedRows,
    resetSelections,
    uncategorizedIsSelected,

    // Business actions
    handleBulkAdd,
    handleBulkIgnore,

    // Loading states
    anyBulkActionIsLoading,
    isAddingResults,
    isIgnoringResults,
  };
};
