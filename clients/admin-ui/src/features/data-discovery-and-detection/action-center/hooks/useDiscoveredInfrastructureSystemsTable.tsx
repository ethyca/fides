import { AntEmpty as Empty } from "fidesui";
import { useCallback, useMemo } from "react";

import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import {
  StagedResourceAPIResponse,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import { useGetIdentityProviderMonitorResultsQuery } from "../../discovery-detection.slice";
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
  // Check if this is an Okta app monitor
  const isOktaApp = monitorId.toLowerCase().includes("okta");

  const tableState = useTableState<"name">({
    sorting: {
      validColumns: ["name"],
    },
  });

  const { pageIndex, pageSize, searchQuery, updateSearch, resetState } =
    tableState;

  // Get regular tabs for non-Okta monitors
  const regularTabs = useActionCenterTabs();

  // Use Identity Provider Monitor endpoint for Okta, otherwise use regular endpoint
  const regularDataQuery = useGetDiscoveredSystemAggregateQuery(
    {
      key: monitorId,
      page: pageIndex,
      size: pageSize,
      search: searchQuery,
      ...(isOktaApp ? {} : regularTabs.activeParams),
    },
    {
      skip: isOktaApp,
    },
  );

  const oktaDataQuery = useGetIdentityProviderMonitorResultsQuery(
    {
      monitor_config_key: monitorId,
      page: pageIndex,
      size: pageSize,
      search: searchQuery,
    },
    {
      skip: !isOktaApp,
    },
  );

  const {
    data: regularData,
    isLoading: regularIsLoading,
    isFetching: regularIsFetching,
  } = regularDataQuery;
  const {
    data: oktaData,
    isLoading: oktaIsLoading,
    isFetching: oktaIsFetching,
  } = oktaDataQuery;

  // Transform Okta data (StagedResourceAPIResponse[]) to SystemStagedResourcesAggregateRecord[]
  // This is a temporary transformation until the BE provides the correct format
  const transformedOktaData = useMemo(() => {
    if (!oktaData?.items) {
      return undefined;
    }

    return {
      ...oktaData,
      items: oktaData.items.map(
        (
          item: StagedResourceAPIResponse,
        ): SystemStagedResourcesAggregateRecord => {
          return {
            id: item.urn,
            name: item.name ?? null,
            system_key: item.system_key ?? null,
            data_uses: item.data_uses ?? [],
            vendor_id: item.vendor_id ?? null,
            total_updates: 1, // Okta apps are individual items, not aggregates
            locations: item.locations ?? [],
            domains: item.domain ? [item.domain] : [],
            // consent_status will be provided by the backend when ready
            // For now, we leave it as null since we don't have the proper format
            consent_status: null,
            metadata: item.metadata ?? null,
          };
        },
      ),
    };
  }, [oktaData]);

  const data = isOktaApp ? transformedOktaData : regularData;
  const isLoading = isOktaApp ? oktaIsLoading : regularIsLoading;
  const isFetching = isOktaApp ? oktaIsFetching : regularIsFetching;

  // For Okta, use simplified tabs (filters should be handled by BE in the future)
  // For regular infrastructure, use standard tabs
  const filterTabs = isOktaApp
    ? [
        {
          label: "All apps",
          hash: "all",
        },
      ]
    : regularTabs.filterTabs;
  const activeTab: string = isOktaApp ? "all" : (regularTabs.activeTab ?? "");
  const activeParams = isOktaApp ? {} : regularTabs.activeParams;

  // Helper function to generate consistent row keys
  const getRecordKey = useCallback(
    (record: SystemStagedResourcesAggregateRecord) =>
      record.id ?? record.vendor_id ?? record.name ?? UNCATEGORIZED_SEGMENT,
    [],
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
    async (tab: string | ActionCenterTabHash) => {
      if (isOktaApp) {
        // For Okta, tab changes will be handled by BE filters in the future
        // For now, we just reset state
      } else {
        await regularTabs.onTabChange(tab as ActionCenterTabHash);
      }
      resetState();
      resetSelections();
    },
    [isOktaApp, regularTabs, resetState, resetSelections],
  );

  const rowClickUrl = useCallback(
    (record: SystemStagedResourcesAggregateRecord) => {
      const recordId = record.id ?? UNCATEGORIZED_SEGMENT;
      const activeTabHash = activeTab ? `#${activeTab}` : "";
      return `${ACTION_CENTER_ROUTE}/${MONITOR_TYPES.INFRASTRUCTURE}/${monitorId}/${recordId}${activeTabHash}`;
    },
    [monitorId, activeTab],
  );

  const { columns } = useDiscoveredInfrastructureSystemsColumns({
    isOktaApp,
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
