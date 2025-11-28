import { AntEmpty as Empty } from "fidesui";
import { useCallback, useMemo } from "react";

import {
  ACTION_CENTER_ROUTE,
  UNCATEGORIZED_SEGMENT,
} from "~/features/common/nav/routes";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { useSearch } from "~/features/common/hooks";
import {
  StagedResourceAPIResponse,
  SystemStagedResourcesAggregateRecord,
} from "~/types/api";

import { useGetIdentityProviderMonitorResultsQuery } from "../../discovery-detection.slice";
import { MONITOR_TYPES } from "../utils/getMonitorType";
import useActionCenterTabs, {
  ActionCenterTabHash,
} from "./useActionCenterTabs";

interface UseDiscoveredInfrastructureSystemsTableConfig {
  monitorId: string;
}

// Extended type to include diff_status for list items
type InfrastructureSystemListItem = SystemStagedResourcesAggregateRecord & {
  diff_status?: string | null;
  urn?: string;
};

export const useDiscoveredInfrastructureSystemsTable = ({
  monitorId,
}: UseDiscoveredInfrastructureSystemsTableConfig) => {
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination({
      defaultPageSize: 50,
    });
  const search = useSearch();

  const tabs = useActionCenterTabs();
  const { activeTab, filterTabs, activeParams, onTabChange } = tabs;

  const oktaDataQuery = useGetIdentityProviderMonitorResultsQuery({
    monitor_config_key: monitorId,
    page: pageIndex,
    size: pageSize,
    search: search.searchQuery,
    diff_status: activeParams.diff_status,
  });

  const {
    data: oktaData,
    isLoading: oktaIsLoading,
    isFetching: oktaIsFetching,
  } = oktaDataQuery;

  const transformedData = useMemo((): {
    items: InfrastructureSystemListItem[];
    total: number;
  } => {
    if (!oktaData?.items) {
      return { items: [], total: 0 };
    }

    const items: InfrastructureSystemListItem[] = oktaData.items.map(
      (item: StagedResourceAPIResponse): InfrastructureSystemListItem => {
        return {
          id: item.urn,
          urn: item.urn,
          name: item.name ?? null,
          system_key: item.system_key ?? null,
          data_uses: item.data_uses ?? [],
          vendor_id: item.vendor_id ?? null,
          total_updates: 1,
          locations: item.locations ?? [],
          domains: item.domain ? [item.domain] : [],
          consent_status: null,
          metadata: item.metadata ?? null,
          diff_status: item.diff_status ?? null,
        };
      },
    );

    return {
      items,
      total: oktaData.total ?? items.length,
    };
  }, [oktaData]);

  const handleTabChange = useCallback(
    async (tab: string | ActionCenterTabHash) => {
      await onTabChange(tab as ActionCenterTabHash);
      resetPagination();
    },
    [onTabChange, resetPagination],
  );

  const rowClickUrl = useCallback(
    (record: InfrastructureSystemListItem) => {
      const recordId = record.urn ?? record.id ?? UNCATEGORIZED_SEGMENT;
      const activeTabHash = activeTab ? `#${activeTab}` : "";
      return `${ACTION_CENTER_ROUTE}/${MONITOR_TYPES.INFRASTRUCTURE}/${monitorId}/${recordId}${activeTabHash}`;
    },
    [monitorId, activeTab],
  );

  return {
    // Data
    data: transformedData,
    isLoading: oktaIsLoading,
    isFetching: oktaIsFetching,

    // Search
    searchQuery: search.searchQuery,
    updateSearch: search.updateSearch,

    // Pagination
    paginationProps,

    // Tabs
    filterTabs,
    activeTab,
    handleTabChange,
    activeParams,

    // Row click handler
    rowClickUrl,

    // Selection helpers
    getRecordKey: useCallback(
      (record: InfrastructureSystemListItem) =>
        record.urn ??
        record.id ??
        record.vendor_id ??
        record.name ??
        UNCATEGORIZED_SEGMENT,
      [],
    ),
  };
};
