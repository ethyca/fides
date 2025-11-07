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
import { MOCK_OKTA_APPS } from "~/mocks/data";
import {
  AlertLevel,
  ConsentAlertInfo,
  DiffStatus,
  StagedResourceAPIResponse,
  StagedResourceTypeValue,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import { OKTA_APP_FILTER_TABS } from "../../constants/oktaAppFilters";
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
  const [oktaActiveTab, setOktaActiveTab] = useState("all");

  const { filterTabs, activeTab, onTabChange, activeParams, actionsDisabled } =
    useActionCenterTabs();

  const tableState = useTableState<DiscoveredSystemAggregateColumnKeys>({
    sorting: {
      validColumns: Object.values(DiscoveredSystemAggregateColumnKeys),
    },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch, resetState } =
    tableState;

  // Check if this is an Okta app monitor
  const isOktaApp = monitorId.toLowerCase().includes("okta");

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

  // Calculate counts for each Okta filter tab
  const oktaFilterCounts = useMemo(() => {
    if (!isOktaApp) {
      return {};
    }

    const counts: Record<string, number> = {};
    OKTA_APP_FILTER_TABS.forEach((tab) => {
      const filteredItems = MOCK_OKTA_APPS.filter((item) => {
        return tab.filter(item as StagedResourceAPIResponse);
      });
      counts[tab.value] = filteredItems.length;
    });

    return counts;
  }, [isOktaApp]);

  // Use mock data for Okta apps and apply filters
  const mockData = useMemo(() => {
    if (!isOktaApp) {
      return null;
    }

    const activeFilter = OKTA_APP_FILTER_TABS.find(
      (tab) => tab.value === oktaActiveTab,
    );
    const filteredItems = MOCK_OKTA_APPS.filter((item) => {
      return activeFilter?.filter(item as StagedResourceAPIResponse);
    });

    return {
      items: filteredItems,
      total: filteredItems.length,
      page: 1,
      size: 50,
      pages: 1,
    };
  }, [isOktaApp, oktaActiveTab]);

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
      return `${ACTION_CENTER_ROUTE}/${monitorType}/${monitorId}/${record.id ?? UNCATEGORIZED_SEGMENT}${activeTab ? `#${activeTab}` : ""}`;
    },

    [monitorId, activeTab, isOktaApp],
  );

  const antTableConfig = useMemo(
    () => ({
      enableSelection: true,
      getRowKey: getRecordKey,
      isLoading: isOktaApp ? false : isLoading,
      isFetching: isOktaApp ? false : isFetching,
      dataSource: isOktaApp ? mockData?.items || [] : data?.items || [],
      totalRows: isOktaApp ? mockData?.total || 0 : data?.total || 0,
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
      mockData,
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
    async (tab: ActionCenterTabHash) => {
      setFirstPageConsentStatus(undefined);
      await onTabChange(tab);
      resetState();
      resetSelections();
    },
    [onTabChange, resetState, resetSelections],
  );

  const { columns } = useDiscoveredSystemAggregateColumns({
    monitorId,
    onTabChange: handleTabChange,
    readonly: actionsDisabled,
    allowIgnore: !activeParams.diff_status.includes(DiffStatus.MUTED),
    consentStatus: firstPageConsentStatus,
    rowClickUrl,
    isOktaApp,
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

    // Okta-specific functionality
    isOktaApp,
    oktaActiveTab,
    setOktaActiveTab,
    oktaFilterCounts,
    oktaFilterTabs: OKTA_APP_FILTER_TABS,
  };
};
