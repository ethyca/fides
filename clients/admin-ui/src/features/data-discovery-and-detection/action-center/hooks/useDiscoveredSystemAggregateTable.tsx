import { AntEmpty as Empty, useToast } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import {
  ACTION_CENTER_ROUTE,
  SYSTEM_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import {
  AntTableHookConfig,
  useAntTable,
  useTableState,
} from "~/features/common/table/hooks";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  AlertLevel,
  ConsentAlertInfo,
  DiffStatus,
  StagedResourceTypeValue,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import {
  useAddMonitorResultSystemsMutation,
  useGetDiscoveredSystemAggregateQuery,
  useIgnoreMonitorResultSystemsMutation,
} from "../action-center.slice";
import { DiscoveredSystemAggregateColumnKeys } from "../constants";
import { SuccessToastContent } from "../SuccessToastContent";
import { MONITOR_TYPES } from "../utils/getMonitorType";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "./useActionCenterTabs";
import { useDiscoveredSystemAggregateColumns } from "./useDiscoveredSystemAggregateColumns";
import { useOktaAppFilters } from "./useOktaAppFilters";

interface UseDiscoveredSystemAggregateTableConfig {
  monitorId: string;
}

export const useDiscoveredSystemAggregateTable = ({
  monitorId,
}: UseDiscoveredSystemAggregateTableConfig) => {
  const router = useRouter();
  const toast = useToast();

  const [firstPageConsentStatus, setFirstPageConsentStatus] = useState<
    ConsentAlertInfo | undefined
  >();

  // Check if this is an Okta app monitor
  const isOktaApp = monitorId.toLowerCase().includes("okta");

  const tableState = useTableState<DiscoveredSystemAggregateColumnKeys>({
    sorting: {
      validColumns: Object.values(DiscoveredSystemAggregateColumnKeys),
    },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch, resetState } =
    tableState;

  // Use appropriate tab management based on monitor type
  const regularTabs = useActionCenterTabs();
  const oktaTabs = useOktaAppFilters({
    pageIndex,
    pageSize,
    searchQuery: searchQuery ?? "",
  });

  // Unify tab interface - use Okta tabs if Okta, otherwise regular tabs
  const filterTabs = isOktaApp ? oktaTabs.filterTabs : regularTabs.filterTabs;
  const activeTab: string = isOktaApp
    ? oktaTabs.activeTab
    : (regularTabs.activeTab ?? "");
  const activeParams = isOktaApp ? {} : regularTabs.activeParams;
  const actionsDisabled = isOktaApp ? false : regularTabs.actionsDisabled;

  const { data, isLoading, isFetching } = useGetDiscoveredSystemAggregateQuery(
    {
      key: monitorId,
      page: pageIndex,
      size: pageSize,
      search: searchQuery,
      ...activeParams,
    },
    {
      skip: isOktaApp, // Skip API call when using mocks
    },
  );

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
      const monitorType = isOktaApp
        ? MONITOR_TYPES.INFRASTRUCTURE
        : MONITOR_TYPES.WEBSITE;
      const recordId = record.id ?? UNCATEGORIZED_SEGMENT;
      const activeTabHash = activeTab ? `#${activeTab}` : "";
      return `${ACTION_CENTER_ROUTE}/${monitorType}/${monitorId}/${recordId}${activeTabHash}`;
    },
    [monitorId, activeTab, isOktaApp],
  );

  const antTableConfig = useMemo(
    () => ({
      enableSelection: true,
      getRowKey: getRecordKey,
      isLoading: isOktaApp ? false : isLoading,
      isFetching: isOktaApp ? false : isFetching,
      dataSource: isOktaApp
        ? oktaTabs.mockData?.items || []
        : data?.items || [],
      totalRows: isOktaApp ? oktaTabs.mockData?.total || 0 : data?.total || 0,
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
    [
      getRecordKey,
      isLoading,
      isFetching,
      data?.items,
      data?.total,
      isOktaApp,
      oktaTabs.mockData,
    ],
  );

  const antTable = useAntTable<
    SystemStagedResourcesAggregateRecord,
    DiscoveredSystemAggregateColumnKeys
  >(
    tableState,
    antTableConfig as AntTableHookConfig<SystemStagedResourcesAggregateRecord>,
  );

  const { selectedRows, resetSelections } = antTable;

  const handleTabChange = useCallback(
    async (tab: string | ActionCenterTabHash) => {
      setFirstPageConsentStatus(undefined);
      if (isOktaApp) {
        await oktaTabs.handleTabChange(tab as string);
      } else {
        await regularTabs.onTabChange(tab as ActionCenterTabHash);
      }
      resetState();
      resetSelections();
    },
    [isOktaApp, oktaTabs, regularTabs, resetState, resetSelections],
  );

  const { columns } = useDiscoveredSystemAggregateColumns({
    monitorId,
    onTabChange: handleTabChange,
    readonly: actionsDisabled,
    allowIgnore: isOktaApp
      ? false
      : !("diff_status" in activeParams) ||
        !(activeParams as { diff_status: DiffStatus[] }).diff_status.includes(
          DiffStatus.MUTED,
        ),
    consentStatus: firstPageConsentStatus,
    rowClickUrl,
    resourceType: isOktaApp ? StagedResourceTypeValue.OKTA_APP : undefined,
  });

  // Business logic effects
  useEffect(() => {
    if (data?.items && !firstPageConsentStatus) {
      // this ensures that the column header remembers the consent status
      // even when the user navigates to a different paginated page
      const consentStatus = data.items.find(
        (item) => item.consent_status?.status === AlertLevel.ALERT,
      )?.consent_status;
      setFirstPageConsentStatus(consentStatus ?? undefined);
    }
  }, [data, firstPageConsentStatus]);

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
              await regularTabs.onTabChange(ActionCenterTabHash.IGNORED);
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
    regularTabs,
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

    // Okta-specific functionality
    isOktaApp,
  };
};
